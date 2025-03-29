import datetime as dt
from django.core.exceptions import ValidationError
from django.urls import reverse


class TreeMixin():
    def clean(self, *args, **kwargs):
        if self.parent:
            if self.pk and self.parent.pk == self.pk:
                raise ValidationError(
                message="Parent cannot be object itself.",
                code="invalid",
            )
            if hasattr(self, "workspace") and self.workspace != self.parent.workspace:
                raise ValidationError(
                    "Workspace should be same as parent's.")
            if hasattr(self, "category") and self.category != self.parent.category:
                raise ValidationError(
                    "Category should be same as parent's.")
        return super().clean(*args, **kwargs)

    @classmethod
    def get_children(cls, obj):
        """
        Returns a dictionary of all children for a given object.
        """
        result = {}
        children = obj.children.all()
        if children.exists:
            for child in children:
                if child.children.all().exists():
                    result[child] = cls.get_children(child)
                else:
                    result[child] = {}
        return result

    @classmethod
    def get_children_pk_list(cls, obj, result=[]):
        """
        Returns a dictionary of all children for a given object.
        """
        children = obj.children.all()
        if children.exists():
            for child in children:
                result.append(child.pk)
                if child.children.all().exists():
                    result.extend(cls.get_children_pk_list(child))
        return result

    @classmethod
    def get_tree(cls, objs):
        """
        Returns a dictionary of tree relationship for given objects.
        """
        result = {}
        root_objs = []
        for obj in objs:
            if obj.parent not in objs:
                root_objs.append(obj)
        for root_obj in root_objs:
            result[root_obj] = cls.get_children(root_obj)
        return result

    @classmethod
    def get_root(cls, obj):
        if obj.parent:
            return cls.get_root(obj.parent)
        else:
            return obj

    @classmethod
    def get_hierarchy(cls, obj):
        root = cls.get_root(obj)
        return {root: cls.get_tree(root.get_children(root))}

    @classmethod
    def _render_hierarchy(cls, tree, attr_name, obj=None):
        result = '<ul>'
        for k, v in tree.items():
            attr_value = getattr(k, attr_name)
            if hasattr(k, "get_absolute_url"):
                url = k.get_absolute_url()
            else:
                url = ""
            if obj and k.pk == obj.pk:
                result += f'''
                <li>
                  <a href="{url}"
                    class="text-warning-emphasis bg-warning-subtle"
                    >{attr_value}</a>
                </li>
                '''
            else:
                result += f'''
                <li>
                  <a href="{k.get_absolute_url()}"
                  class="link-secondary"
                  >{attr_value}</a>
                </li>
                '''
            if v:
                result += cls._render_hierarchy(v, attr_name, obj)
        result += '</ul>'
        return result

    def render_hierarchy(self, attr_name):
        return self._render_hierarchy(self.get_hierarchy(self), attr_name, self)

    @classmethod
    def render_tree(cls, tree, attr_name):
        result = '<ul>'
        for k, v in tree.items():
            attr_value = getattr(k, attr_name)
            if hasattr(k, "get_absolute_url"):
                url = k.get_absolute_url()
            else:
                url = ""
            result += f'''
            <li>
              <a href="{url}"
                class="link-secondary"
                >{attr_value}</a>
            </li>
            '''
            if v:
                result += cls.render_tree(v, attr_name)
        result += '</ul>'
        return result


class CommentMixin():
    def get_content_display(self):
        content_display = ' '.join(self.content.split()[0:5]) + "..."
        return f'{content_display}'

    @classmethod
    def render_comments_tree(cls, tree):
        if tree:
            result = '<ul>'
            for k, v in tree.items():
                url_update = reverse(
                    f"demo:task-comment-update", kwargs={"pk": k.pk})
                url_delete = reverse(
                    f"demo:task-comment-delete", kwargs={"pk": k.pk})
                updated_at_display = dt.datetime.strftime(
                    k.updated_at, '%d-%m-%Y %H-%M %p')
                result += f'''
                <li>
                    <span>@{k.created_by} (on {updated_at_display}) </span>
                    <span style="display:inline-block; width: .25rem;"></span>
                    <span>
                      <a href="{url_update}"
                        class="text-primary-emphasis bg-primary-subtle">Update</a>
                      <span style="display:inline-block; width: .25rem;"></span>
                      <a href="{url_delete}" 
                        class="text-danger-emphasis bg-danger-subtle">Delete</a>
                    </span>
                    <br>
                    <span class="fs-4">{k.content}</span>
                </li>
                '''
                if v:
                    result += cls.render_comments_tree(v)
            result += '</ul>'
        else:
            result = ''
        return result

