
__version__ = '0.0.1'
from one_wiki.overrides.wiki_page import get_context,update_context_
from one_wiki.overrides.overrides import set_template_path,update_page_
from wiki.wiki.doctype.wiki_page.wiki_page import WikiPage
from frappe.website.page_renderers.document_page import DocumentPage 
from frappe.website.page_renderers.template_page import TemplatePage
from wiki.www import edit
from wiki.www import new
from wiki.www import drafts
from one_wiki.www.wiki.edit import get_context as get_edit_context
from one_wiki.www.drafts import get_context as get_draft_context
from one_wiki.www.new import get_context as get_new_context

WikiPage.get_context = get_context
edit.get_context = get_edit_context
drafts.get_context = get_draft_context
new.get_context = get_new_context
WikiPage.update_page = update_page_
DocumentPage.update_context = update_context_
TemplatePage.set_template_path=set_template_path


