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

data["name"] = "Plugin Compatibility"
data["jobs"]["check_for_tests"]["runs-on"] = "ubuntu-latest"
data["jobs"]["tests"]["runs-on"] = "ubuntu-latest"
data["jobs"]["tests"]["container"] = "discourse/discourse_test:slim${{ (matrix.build_type == 'frontend' || matrix.build_type == 'system') && '-browsers' || '' }}"

# override on
injection = """
  workflow_dispatch:

"""
data['on'] = yaml.load(injection)

# remove jobs.linting
data['jobs'].pop('linting')

# inject jobs.check_for_tests
injection_steps = r"""
- name: Checkout repo
  uses: actions/checkout@v4
  with:
    path: tmp

- name: Setup Plugin Directory
  run: mkdir -p plugins

- name: Clone plugins
  uses: discourse/.github/actions/clone-additional-plugins@b780a606cbe5c865c51016699a1831698e3126ee
  with:
    ssh_private_key: ${{ secrets.ssh_private_key || ''}}
    about_json_path: tmp/plugins.json

- name: Check For Test Types
  id: check_tests
  shell: ruby {0}
  working-directory: plugins
  run: |

    require 'json'

    matrix = []

    matrix << 'frontend' if Dir.glob("*/test/javascripts/**/*.{js,gjs}").any?
    matrix << 'backend'
    matrix << 'system' if Dir.glob("*/spec/system/**/*.rb").any?

    puts "Running jobs: #{matrix.inspect}"

    File.write(ENV["GITHUB_OUTPUT"], "has_specs=true\n", mode: 'a+') if Dir.glob("*/spec/**/*.rb").reject { _1.include?("spec/system") }.any?

    File.write(ENV["GITHUB_OUTPUT"], "matrix=#{matrix.to_json}\n", mode: 'a+')

"""
data['jobs']['check_for_tests']['steps'] = yaml.load(injection_steps)

jobs_tests_env = data['jobs']['tests']['env']
jobs_tests_env['PLUGIN_NAME'] = '*'

jobs_tests_steps = data['jobs']['tests']['steps']
def find_step_by_name(steps, name):
    for step in steps:
        if 'name' in step and step['name'] == name:
            return step
def remove_step_by_name(steps, name):
    steps.remove(find_step_by_name(steps, name))
def insert_step_after(steps, step, after_name):
    for i, s in enumerate(steps):
        if 'name' in s and s['name'] == after_name:
            steps.insert(i + 1, step)
            return
    raise ValueError(f"Step with name '{after_name}' not found")

remove_step_by_name(jobs_tests_steps, 'Install plugin')
remove_step_by_name(jobs_tests_steps, 'Clone additional plugins')
remove_step_by_name(jobs_tests_steps, 'Validate discourse-compatibility')
remove_step_by_name(jobs_tests_steps, 'Check Annotations')
injection_steps = r"""
- name: Checkout plugins list
  uses: actions/checkout@v4
  with:
    path: tmp

- name: Clone plugins
  uses: discourse/.github/actions/clone-additional-plugins@v1
  with:
    ssh_private_key: ${{ secrets.ssh_private_key || ''}}
    about_json_path: tmp/plugins.json

"""
for step in yaml.load(injection_steps)[::-1]:
    insert_step_after(jobs_tests_steps, step, 'Setup gems')

yaml.dump(data, target)