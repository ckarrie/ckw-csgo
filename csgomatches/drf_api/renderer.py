from rest_framework.renderers import BrowsableAPIRenderer


class CSGOMatchesBrowseAPIRenderer(BrowsableAPIRenderer):
    template = 'csgomatches/rest_framework/csgo_api.html'
    format = 'api_csgo'