from thisisthesitebuilder.pages.models import Page


class PageBuilder(object):
    def __init__(self, build_meta, force_rebuild=False):
        self.build_meta = build_meta
        self.force_rebuild = force_rebuild

    def build_page(self, page_name, template_name=None, root=False, active_context=None,
                   passive_context=None, compact=False, force_rebuild=None):
        '''
        Takes a page name, checks to see if custom template or YAML files exist, writes HTML to frontend.
        '''
        if force_rebuild is None:
            force_rebuild = self.force_rebuild

        page = Page(page_name, self.build_meta, template_name=template_name, root=root,
                    active_context=active_context, passive_context=passive_context, compact=compact, force_rebuild=force_rebuild)

        #######################

        yaml_filename = (
        "%s/authored/pages/%s" % (self.build_meta['data_dir'], page.full_page_name)).replace(
            ".html",
            ".yaml")

        page.update_from_yaml(yaml_filename)

        page.render()

        if page.updated:
            with open("%s/%s" % (self.build_meta['frontend_dir'], page.output_filename), "w+") as f:
                f.write(page.html)

        return page

