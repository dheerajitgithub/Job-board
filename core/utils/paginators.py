from django.core.paginator import Paginator

def get_paginated_data(request, queryset, page=None, per_page=15, **kwargs):
    """custom pagination with page number"""
    effective_per_page = per_page
    if len(queryset) < per_page:
        effective_per_page = len(queryset)
    paginator = Paginator(queryset, per_page)
    data_dict = {"count":len(queryset),"results": []}

    if page and effective_per_page > 0:
        try:
            page_data = paginator.page(page)

            data_dict["results"] = page_data.object_list
            if page_data.has_previous():
                data_dict["previous"] = (request.build_absolute_uri(request.path)
                                         +
                                         f'?page={page_data.previous_page_number()}')
            else:
                data_dict["previous"] = None
            if page_data.has_next():
                data_dict["next"] = (request.build_absolute_uri(request.path)
                                     +
                                     f'?page={page_data.next_page_number()}')
            else:
                data_dict["next"] = None
            data_dict["num_pages"] = paginator.num_pages
        except Exception:
            pass
    else:
        data_dict["results"] = queryset
        data_dict["num_pages"] = 1
        data_dict["previous"] = None
        data_dict["next"] = None
    data_dict.update(kwargs)
    return data_dict


def get_paginated_data_socket(queryset, page=None, per_page=15, **kwargs):
    """custom pagination with page number - websockets"""

    effective_per_page = per_page
    if len(queryset) < per_page:
        effective_per_page = len(queryset)
    paginator = Paginator(queryset, per_page)
    data_dict = {"count":len(queryset),"results": []}

    if page and effective_per_page > 0:
        try:
            page_data = paginator.page(page)

            data_dict["results"] = page_data.object_list
            if page_data.has_previous():
                data_dict["previous"] = True
            else:
                data_dict["previous"] = False
            if page_data.has_next():
                data_dict["next"] = True
            else:
                data_dict["next"] = False
            data_dict["num_pages"] = paginator.num_pages
        except Exception:
            pass
    else:
        data_dict["results"] = queryset
        data_dict["num_pages"] = 1
        data_dict["previous"] = None
        data_dict["next"] = None
    data_dict.update(kwargs)
    return data_dict
