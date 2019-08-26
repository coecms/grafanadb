#!/usr/bin/env python
#
# Copyright 2019 Scott Wales
#
# Author: Scott Wales <scott.wales@unimelb.edu.au>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from flask import Flask, request, jsonify, abort
from jsonschema import validate
from grafanadb.find import find_impl, du_impl
from grafanadb.db import connect

app = Flask(__name__)
app.config['DATABASE'] = 'postgresql://localhost:5432/grafana'

find_schema = {
        'type': 'object',
        'properties': {
            'root_inodes': {
                'type': 'array',
                'contains': {
                    'type': 'array',
                    'items': [
                        {'type': 'number'},
                        {'type': 'number'},
                    ],
                    },
                },
            'gid': {'type': ['number', 'null']},
            'not_gid': {'type': ['number', 'null']},
            'uid': {'type': ['number', 'null']},
            'not_uid': {'type': ['number', 'null']},
            'mtime': {'type': ['number', 'null']},
            'size': {'type': ['number', 'null']},
        }
    }

@app.route('/find')
def find():
    try:
        json = request.get_json()
        validate(json, schema=find_schema)

        q = find_impl(**json)
        with connect(url=app.config['DATABASE']) as conn:
            return jsonify([row.path for row in conn.execute(q)])
    except:
        abort(400)

@app.route('/du')
def du():
    json = request.get_json()
    validate(json, schema=find_schema)

    q = du_impl(**json)
    with connect(url=app.config['DATABASE']) as conn:
        r = conn.execute(q).fetchone()
        return {'size': float(r.size) if r.size is not None else 0.0, 'inodes': r.inodes}
