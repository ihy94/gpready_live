from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from collections import OrderedDict

class DefaultPagination(PageNumberPagination):
  page_size = 10
  page_size_query_param = 'page_size'

  def get_paginated_response(self, data):
      return Response(OrderedDict([
          ('count', self.page.paginator.count),
          ('next', self.get_next_link()),
          ('per_page',self.page_size),
          ('previous', self.get_previous_link()),
          ('results', data)
      ]))

