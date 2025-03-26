from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DrfVE
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError as DjVE
import copy


class CustomBaseSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        # user = self.context["request"].user
        # validated_data.update(created_by=user)
        data_copy = copy.deepcopy(validated_data)
        with transaction.atomic(savepoint=True, durable=False):
            try:
                instance_tmp = super().create(data_copy)
                instance_tmp.full_clean()
            except (DjVE, IntegrityError) as e:
                raise DrfVE(e)
            finally:
                transaction.set_rollback(True)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        # user = self.context["request"].user
        # validated_data.update(created_by=user)
        data_copy = copy.deepcopy(validated_data)
        with transaction.atomic(savepoint=True, durable=False):
            try:
                instance = super().update(instance, data_copy)
                instance.full_clean()
            except (DjVE, IntegrityError) as e:
                transaction.set_rollback(True)
                raise DrfVE(e)
            except Exception as e:
                transaction.set_rollback(True)
                raise DrfVE(f'Unknown error: {e}')
            else:
                if self.is_valid(raise_exception=True):
                    instance.save()
                    return instance
