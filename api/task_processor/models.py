import pickle
import typing
import uuid

from django.db import models


class Task(models.Model):
    uuid = models.UUIDField(unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_for = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    pickled_callable = models.BinaryField()
    pickled_args = models.BinaryField(blank=True, null=True)
    pickled_kwargs = models.BinaryField(blank=True, null=True)

    @classmethod
    def create(cls, callable_: typing.Callable, *args, **kwargs) -> "Task":
        return Task(
            pickled_callable=pickle.dumps(callable_),
            pickled_args=pickle.dumps(args),
            pickled_kwargs=pickle.dumps(kwargs),
        )

    def run(self):
        return self._callable(*self._args, **self._kwargs)

    @property
    def _callable(self) -> typing.Callable:
        return pickle.loads(self.pickled_callable)

    @property
    def _args(self) -> typing.List[typing.Any]:
        return pickle.loads(self.pickled_args)

    @property
    def _kwargs(self) -> typing.Dict[str, typing.Any]:
        return pickle.loads(self.pickled_kwargs)
