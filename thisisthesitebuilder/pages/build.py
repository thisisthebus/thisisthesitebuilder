from thisisthesitebuilder.pages.models import Page


class PageBuilder(object):
    def __init__(self, build_meta, force_rebuild=False):
        self.build_meta = build_meta
        self.force_rebuild = force_rebuild

    def build_page(self, name, directory=None, template_name=None, root=False, active_context=None,
                   passive_context=None, compact=False, force_rebuild=None):
        '''
        Takes a page name, checks to see if custom template or YAML files exist, writes HTML to frontend directory as defined in self.build_meta.
        '''
        if force_rebuild is None:
            force_rebuild = self.force_rebuild

        page = Page(name, self.build_meta, directory=directory, template_name=template_name, root=root,
                    active_context=active_context, passive_context=passive_context, compact=compact,
                    force_rebuild=force_rebuild)

        #######################  Make sure directory exists

        yaml_filename = (
            "%s/authored/pages/%s" % (self.build_meta['data_dir'], page.full_name)).replace(
            ".html",
            ".yaml")

        page.update_from_yaml(yaml_filename)

        page.render(force_rebuild=True)

        if page.updated:
            final_output_filename = "%s/%s" % (self.build_meta['frontend_dir'], page.output_filename)
            with open(final_output_filename, "w+") as f:
                f.write(page.html)

        return page
