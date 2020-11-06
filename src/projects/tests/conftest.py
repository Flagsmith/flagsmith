import pytest

from organisations.models import Organisation
from projects.models import Project
from segments.models import Segment


@pytest.fixture()
def organisation():
    return Organisation.objects.create(name='Test Organisation')


@pytest.fixture()
def project(organisation):
    return Project.objects.create(name='Test Project', organisation=organisation)


@pytest.fixture()
def segments(project):
    segments = []
    for i in range(3):
        segments.append(Segment.objects.create(name=f'Test Segment {i}', project=project))
    return segments
