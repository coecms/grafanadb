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

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

engine = None

Session = sessionmaker()


@contextmanager
def connect(url="postgresql://localhost:9876/grafana"):
    """
    Get a connection to the database (context manager)::

        with connect() as conn:
            conn.execute(q)
    """
    global engine
    if engine is None:
        engine = sa.create_engine(url)
        Session.configure(bind=engine)

    conn = engine.connect()

    yield conn

    conn.close()
