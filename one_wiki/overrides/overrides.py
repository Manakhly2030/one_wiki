import frappe
import re
import os
from frappe.website.utils  import is_binary_file
from frappe.desk.form.assign_to import add
# from frappe.website.website_generator import WebsiteGenerator




def update_page_(doc, title, content, edit_message, raised_by=None):
	"""
	Update Wiki Page and create a Wiki Page Revision
	"""
	doc.title = title
	
	if content != doc.content:
		doc.content = content
		revision = frappe.new_doc("Wiki Page Revision")
		revision.append("wiki_pages", {"wiki_page": doc.name})
		revision.content = content
		revision.message = edit_message
		revision.raised_by = raised_by
		revision.insert()

	doc.save()






def wiki_patch_submit(doc,ev):
	"""Close the existing todo when the document is about to be approved.

	Args:
		doc Wiki Page Patch
		ev event
	"""
	todos = frappe.get_all("ToDo",{"reference_type":doc.doctype,'reference_name':doc.name})
	if todos:
		for each in todos:
			frappe.db.set_value("ToDo",each.name,'status','Closed')
		frappe.db.commit()
	

def wiki_patch_insert(doc,ev):
	"""Create  an approval Todo for the current user's line manager when a wiki page patch is created

	Args:
		doc Wiki Page Patch
		ev event
	"""
	
	reports_to = frappe.get_all("Employee",{'user_id':frappe.session.user},['employee_name','reports_to'])
	 #Set Approver as the user
	if not reports_to:
		reports_to = frappe.session.user
	if reports_to:
		if reports_to[0].get('employee_name') and reports_to[0].get('reports_to'):
			reports_user = frappe.get_value("Employee",reports_to[0].reports_to,'user_id')
			drafts_url = frappe.utils.get_url()+"/drafts"
			if reports_user:
				args = {
						'assign_to':[reports_user],
						'doctype':doc.doctype,
						'name':doc.name,
						'description':f"Please note that {reports_to[0].employee_name} just modified the Wiki page titled <b>\
          								{doc.new_title}</b><br>.You can approve this on the drafts page <a href='{drafts_url}'>\
                      						here</a> <br/> \
							Kindly review the changes made.",
					}
				add(args)
				doc.approved_by = reports_user
				doc.save()
				frappe.db.commit()
    
			


def get_start_folders():
	return frappe.local.flags.web_pages_folders or ("www", "templates/pages")


def set_template_path(selfs):
	"""
	Searches for file matching the path in the /www
	and /templates/pages folders and sets path if match is found
	"""
	folders = get_start_folders()
	for app in frappe.get_installed_apps(frappe_last=True,sort=True):
		app_path = frappe.get_app_path(app)

		for dirname in folders:
			search_path = os.path.join(app_path, dirname, selfs.path)
			for file_path in selfs.get_index_path_options(search_path):
				if os.path.isfile(file_path) and not is_binary_file(file_path):
					selfs.app = app
					selfs.app_path = app_path
					selfs.file_dir = dirname
					selfs.basename = os.path.splitext(file_path)[0]
					selfs.template_path = os.path.relpath(file_path, selfs.app_path)
					selfs.basepath = os.path.dirname(file_path)
					selfs.filename = os.path.basename(file_path)
					selfs.name = os.path.splitext(selfs.filename)[0]
					return


@frappe.whitelist()
def get_context(doc, context):
	doc.verify_permission("read")
	doc.set_breadcrumbs(context)
	wiki_settings = frappe.get_single("Wiki Settings")
	context.navbar_search = wiki_settings.add_search_bar
	context.banner_image = wiki_settings.logo
	context.script = wiki_settings.javascript
	context.docs_search_scope = doc.get_docs_search_scope()
	context.metatags = {
		"title": doc.title, 
		"description": doc.meta_description,
		"keywords": doc.meta_keywords,
		"image": doc.meta_image,
		"og:image:width": "1200",
		"og:image:height": "630",
		}
	context.last_revision = doc.get_last_revision()
	context.number_of_revisions = frappe.db.count(
		"Wiki Page Revision Item", {"wiki_page": doc.name}
	)
	html = md_to_html(doc.content)
	context.content = html
	context.page_toc_html = html.toc_html
	context.show_sidebar = True
	context.hide_login = True
	context.lang = frappe.local.lang

	context = context.update(
		{
			"post_login": [
				{"label": ("My Account"), "url": "/me"},
				{"label": ("Logout"), "url": "/?cmd=web_logout"},
				{
					"label": ("Contributions ") + get_open_contributions(),
					"url": "/contributions",
				},
				{
					"label": ("My Drafts ") + get_open_drafts(),
					"url": "/drafts",
				},
			]
		}
	)


def md_to_html(markdown_text: str):
	from markdown2 import MarkdownError
	from markdown2 import markdown as _markdown
	name = re.findall(r'[\u0600-\u06FF]+',markdown_text)

	if name:
		markdown_text = '<p style="text-align: right;">'+markdown_text+'</p>'
	extras = {
		"fenced-code-blocks": None,
		"tables": None,
		"header-ids": None,
		"toc": None,
		"highlightjs-lang": None,
		"html-classes": {"table": "table table-bordered", "img": "screenshot",},
	}

	try:
		return _markdown(markdown_text or "", extras=extras)
	except MarkdownError:
		pass

def get_open_contributions():
	count = len(
		frappe.get_list("Wiki Page Patch", filters=[["status", "=", "Under Review"]],)
	)
	return f'<span class="count">{count}</span>'

def get_open_drafts():
	count = len(
		frappe.get_list("Wiki Page Patch", filters=[["status", "=", "Draft"], ["owner", '=', frappe.session.user]],)
	)
	return f'<span class="count">{count}</span>'

@frappe.whitelist()
def preview(content, name, new, type, diff_css=False):
	html = md_to_html(content)
	if new:
		return {"html": html}
	from ghdiff import diff

	old_content = frappe.db.get_value("Wiki Page", name, "content")
	diff = diff(old_content, content, css=diff_css)
	return {
		"html": html,
		"diff": diff,
		"orignal_preview": md_to_html(old_content),
	}
