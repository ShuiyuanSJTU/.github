from ruamel.yaml import YAML
from pathlib import Path
import sys

if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <source> <target>")
    sys.exit(1)

source = Path(sys.argv[1])
target = Path(sys.argv[2])

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 4096
yaml.indent(mapping=2, sequence=4, offset=2)

data = yaml.load(source)

# inject on.workflow_call.inputs.linting
on_workflow_call_inputs = data['on']['workflow_call']['inputs']
if 'linting' in on_workflow_call_inputs:
    raise RuntimeWarning("linting already exists in on.workflow_call.inputs")
else:
    injection = """
        description: "Run linting checks"
        type: boolean
        default: false
        required: false
    """
    on_workflow_call_inputs.insert(0, 'linting', yaml.load(injection))

# inject job.linting.if
jobs_linting = data['jobs']['linting']
if 'if' in jobs_linting:
    raise RuntimeWarning("if already exists in jobs.linting")
else:
    jobs_linting.insert(0, 'if', "${{ inputs.linting }}")

yaml.dump(data, target)