from rest_framework import pagination

from .constants import MAX_PAGINATION, PAGINATION_SIZE


class CustomPagination(pagination.PageNumberPagination):
    max_page_size = MAX_PAGINATION
    page_size = PAGINATION_SIZE

    def get_page_size(self, request):
        page_size = request.query_params.get('limit', None)
        if page_size is not None:
            try:
                return min(int(page_size), self.max_page_size)
            except ValueError:
                return self.page_size
        return self.page_size
