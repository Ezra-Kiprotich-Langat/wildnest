from rest_framework.pagination import PageNumberPagination, LimitOffsetPagination

class StandardPagination(PageNumberPagination):

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return super().get_paginated_response(data)
    
    def get_paginated_response_schema(self, schema):
        return {
            'type': 'object',
            'properties': {
                'count': {'type': 'integer', 'example': 123},
                'next': {'type': 'string', 'nullable': True, 'format': 'uri'},
                'previous': {'type': 'string', 'nullable': True, 'format': 'uri'},
                'results': schema,
            },
        }


class SmallPagination(PageNumberPagination):
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class LargePagination(PageNumberPagination):
   
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class LimitOffsetPaginationClass(LimitOffsetPagination):
    
    default_limit = 20
    max_limit = 100