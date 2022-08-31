#!/usr/bin/env python3

import re
import sys

enums = {}
unions = {}
tables = {}

dbscheme = sys.argv[1] if len(sys.argv) >= 2 else '../ql/lib/config/semmlecode.dbscheme'

def parse_dbscheme(filename):
    with open(filename, 'r') as f:
        dbscheme = f.read()

    # Remove comments
    dbscheme = re.sub(r'/\*.*?\*/', '', dbscheme, flags=re.DOTALL)
    dbscheme = re.sub(r'//[^\r\n]*', '', dbscheme)

    # kind enums
    for name, kind, body in re.findall(r'case\s+@([^.\s]*)\.([^.\s]*)\s+of\b(.*?);',
                                       dbscheme,
                                       flags=re.DOTALL):
        mapping = []
        for num, typ in re.findall(r'(\d+)\s*=\s*@(\S+)', body):
            mapping.append((int(num), typ))
        enums[name] = (kind, mapping)

    # unions
    for name, rhs in re.findall(r'@(\w+)\s*=\s*(@\w+(?:\s*\|\s*@\w+)*)',
                                dbscheme,
                                flags=re.DOTALL):
        typs = re.findall(r'@(\w+)', rhs)
        unions[name] = typs

    # tables
    for relname, body in re.findall('\n([\w_]+)(\([^)]*\))',
                                    dbscheme,
                                    flags=re.DOTALL):
        columns = list(re.findall('(\S+)\s*:\s*([^\s,]+)(?:\s+(ref)|)', body))
        tables[relname] = columns

parse_dbscheme(dbscheme)

type_aliases = {}

for alias, typs in unions.items():
    if len(typs) == 1:
        real = typs[0]
        if real in type_aliases:
            real = type_aliases[real]
        type_aliases[alias] = real

def unalias(t):
    return type_aliases.get(t, t)

type_leaf = set()
type_union = {}

for name, (kind, mapping) in enums.items():
    s = set()
    for num, typ in mapping:
        s.add(typ)
        type_leaf.add(typ)
    type_union[name] = s

for name, typs in unions.items():
    if name not in type_aliases:
        type_union[name] = set(map(unalias, typs))

for relname, columns in tables.items():
    for _, db_type, ref in columns:
        if db_type[0] == '@' and ref == '':
            db_type_name = db_type[1:]
            if db_type_name not in enums:
                type_leaf.add(db_type_name)

type_union_of_leaves = {}

def to_leaves(t):
    if t not in type_union_of_leaves:
        xs = type_union[t]
        leaves = set()
        for x in xs:
            if x in type_leaf:
                leaves.add(x)
            else:
                to_leaves(x)
                leaves.update(type_union_of_leaves[x])
        type_union_of_leaves[t] = leaves

for t in type_union:
    to_leaves(t)

supertypes = {}
for t in type_leaf:
    supers = set()
    for sup, s in type_union_of_leaves.items():
        if t in s:
            supers.add(sup)
    supertypes[t] = supers
for t, leaves in type_union_of_leaves.items():
    supers = set()
    for sup, s in type_union_of_leaves.items():
        if t != sup and leaves.issubset(s):
            supers.add(sup)
    supertypes[t] = supers

def upperFirst(string):
    return string[0].upper() + string[1:]

def genTable(kt, relname, columns, enum = None, kind = None, num = None, typ = None):
    kt.write('fun TrapWriter.write' + upperFirst(relname))
    if kind is not None:
        kt.write('_' + typ)
    kt.write('(')
    for colname, db_type, _ in columns:
        if colname != kind:
            kt.write(colname + ': ')
            if db_type == 'int':
                kt.write('Int')
            elif db_type == 'float':
                kt.write('Double')
            elif db_type == 'string':
                kt.write('String')
            elif db_type == 'date':
                kt.write('Date')
            elif db_type == 'boolean':
                kt.write('Boolean')
            elif db_type[0] == '@':
                label = db_type[1:]
                if label == enum:
                    label = typ
                kt.write('Label<out Db' + upperFirst(label) + '>')
            else:
                raise Exception('Bad db_type: ' + db_type)
            kt.write(', ')
    kt.write(') {\n')
    kt.write('    this.writeTrap("' + relname + '(')
    comma = ''
    for colname, db_type, _ in columns:
        kt.write(comma)
        if colname == kind:
            kt.write(str(num))
        elif db_type == 'string':
            kt.write('\\"${this.escapeTrapString(this.truncateString(' + colname + '))}\\"')
        elif db_type == 'date':
            kt.write('D\\"${' + colname + '}\\"')
        else:
            kt.write('$' + colname)
        comma = ', '
    kt.write(')\\n")\n')
    kt.write('}\n')

with open('src/main/kotlin/KotlinExtractorDbScheme.kt', 'w') as kt:
    kt.write('/* Generated by ' + sys.argv[0] + ': Do not edit manually. */\n')
    kt.write('package com.github.codeql\n')
    kt.write('import java.util.Date\n')

    for relname, columns in tables.items():
        enum = None
        for _, db_type, ref in columns:
            if db_type[0] == '@' and ref == '':
                db_type_name = db_type[1:]
                if db_type_name in enums:
                    enum = db_type_name
        if enum is None:
            genTable(kt, relname, columns)
        else:
            (kind, mapping) = enums[enum]
            for num, typ in mapping:
                genTable(kt, relname, columns, enum, kind, num, typ)

    kt.write('sealed interface AnyDbType\n')
    for typ in sorted(supertypes):
        kt.write('sealed interface Db' + upperFirst(typ) + ': AnyDbType')
        # Sorting makes the output deterministic.
        names = sorted(supertypes[typ])
        kt.write(''.join(map(lambda name: ', Db' + upperFirst(name), names)))
        kt.write('\n')
    for alias in sorted(type_aliases):
        kt.write('typealias Db' + upperFirst(alias) + ' = Db' + upperFirst(type_aliases[alias]) + '\n')