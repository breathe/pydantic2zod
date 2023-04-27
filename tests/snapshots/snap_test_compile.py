# -*- coding: utf-8 -*-
# snapshottest: v1 - https://goo.gl/zC4yUc
from __future__ import unicode_literals

from snapshottest import Snapshot


snapshots = Snapshot()

snapshots['test_initializes_empty_lists 1'] = '''
/**
 * NOTE: automatically generated by the pydantic2zod compiler.
 */

import { z } from "zod";

export const Class = z.object({
  methods: z.array(z.string()).default([]),
  dunder_methods: z.array(z.string()).default([]),
});
export type ClassType = z.infer<typeof Class>;
'''

snapshots['test_renames_models_based_on_given_rules 1'] = '''
/**
 * NOTE: automatically generated by the pydantic2zod compiler.
 */

import { z } from "zod";

export const Class = z.object({
  name: z.string(),
});
export type ClassType = z.infer<typeof Class>;

export const BaseClass = z.object({
  name: z.string(),
  methods: z.array(z.string()),
});
export type BaseClassType = z.infer<typeof BaseClass>;

export const Module = z.object({
  name: z.string(),
  classes: z.array(BaseClass),
});
export type ModuleType = z.infer<typeof Module>;
'''
