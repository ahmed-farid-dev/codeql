// generated by codegen/codegen.py
import codeql.swift.elements
import TestUtils

from ImportDecl x, ModuleDecl getModule, string isExported
where
  toBeTested(x) and
  not x.isUnknown() and
  getModule = x.getModule() and
  if x.isExported() then isExported = "yes" else isExported = "no"
select x, "getModule:", getModule, "isExported:", isExported