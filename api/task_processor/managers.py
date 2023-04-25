from django.db.models import Manager


class TaskManager(Manager):
    def get_tasks_to_process(self, num_tasks):
        return self.raw("SELECT * FROM get_tasks_to_process(%s)", [num_tasks])


class RecurringTaskManager(Manager):
    def get_tasks_to_process(self, num_tasks):
        return self.raw("SELECT * FROM get_recurringtasks_to_process(%s)", [num_tasks])
