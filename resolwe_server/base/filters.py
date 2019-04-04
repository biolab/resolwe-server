"""Django filters."""
from __future__ import absolute_import, division, print_function, unicode_literals

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import FieldDoesNotExist
from django.db import connection
from django.db.models.expressions import RawSQL

from rest_framework.filters import OrderingFilter
import django_filters as filters

from resolwe.flow.filters import NUMBER_LOOKUPS, TEXT_LOOKUPS


class JsonOrderingFilter(OrderingFilter):
    """Ordering filter for JSON fields.

    Without proper indices, such orderings may be inefficient. All
    JSON paths will be treated as strings.

    """

    def remove_invalid_fields(self, queryset, fields, view, request):
        """Remove invalid fields."""
        order_fields = []
        for field in fields:
            # When a dot is present in the order field, treat it as a JSON path.
            if '.' not in field:
                order_fields.extend(
                    super(JsonOrderingFilter, self).remove_invalid_fields(
                        queryset, [field], view, request
                    )
                )
                continue

            path = field.split('.')
            base_field = path[0]
            if len(path) < 2:
                continue
            if not super(JsonOrderingFilter, self).remove_invalid_fields(
                queryset, [base_field], view, request
            ):
                continue

            reverse = False
            if base_field[0] == '-':
                base_field = base_field[1:]
                reverse = True

            # Resolve base field.
            try:
                quote_name = connection.ops.quote_name
                model_meta = queryset.model._meta  # pylint: disable=protected-access
                base_field = '{}.{}'.format(
                    quote_name(model_meta.db_table),
                    quote_name(model_meta.get_field(base_field).column),
                )
            except FieldDoesNotExist:
                continue

            placeholders = '->'.join(['%s'] * (len(path) - 2))
            # The last placeholder should be accessed via the ->> operator.
            if placeholders:
                placeholders = '->{}->>%s'.format(placeholders)
            else:
                placeholders = '->>%s'

            expression = RawSQL(
                # We can use base_field here directly because we've resolved it via Django ORM.
                '{}{}'.format(base_field, placeholders),
                params=path[1:],
            )

            if reverse:
                expression = expression.desc()

            order_fields.append(expression)

        return order_fields


class GroupFilter(filters.FilterSet):
    """Filter the Group endpoint."""

    class Meta:
        """Filter configuration."""

        model = Group
        fields = {
            'id': NUMBER_LOOKUPS[:],
            'name': TEXT_LOOKUPS[:],
        }


class UserFilter(filters.FilterSet):
    """Filter the User endpoint."""

    job_title = filters.CharFilter(field_name='profile__job_title')
    company = filters.CharFilter(field_name='profile__company')
    department = filters.CharFilter(field_name='profile__department')
    location = filters.CharFilter(field_name='profile__location')
    lab = filters.CharFilter(field_name='profile__lab')
    newsletter = filters.rest_framework.filters.BooleanFilter(field_name='profile__newsletter')
    groups = filters.ModelChoiceFilter(queryset=Group.objects.all())

    class Meta:
        """Filter configuration."""

        model = get_user_model()
        fields = {
            'id': NUMBER_LOOKUPS[:],
            'username': TEXT_LOOKUPS[:],
            'first_name': TEXT_LOOKUPS[:],
            'last_name': TEXT_LOOKUPS[:],
        }