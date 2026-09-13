from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import match
from inspect_ai.solver import generate

@task
def local_baseline():
    return Task(
        dataset=[
            Sample(
                input="Return exactly the token ROUTE_OK and nothing else.",
                target="ROUTE_OK",
            )
        ],
        solver=generate(),
        scorer=match(),
    )
