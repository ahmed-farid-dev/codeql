// generated by codegen/codegen.py
import codeql.swift.elements
import TestUtils

from
  AccessorDecl x, ModuleDecl getModule, Type getInterfaceType, string getName, string isGetter,
  string isSetter, string isWillSet, string isDidSet
where
  toBeTested(x) and
  not x.isUnknown() and
  getModule = x.getModule() and
  getInterfaceType = x.getInterfaceType() and
  getName = x.getName() and
  (if x.isGetter() then isGetter = "yes" else isGetter = "no") and
  (if x.isSetter() then isSetter = "yes" else isSetter = "no") and
  (if x.isWillSet() then isWillSet = "yes" else isWillSet = "no") and
  if x.isDidSet() then isDidSet = "yes" else isDidSet = "no"
select x, "getModule:", getModule, "getInterfaceType:", getInterfaceType, "getName:", getName,
  "isGetter:", isGetter, "isSetter:", isSetter, "isWillSet:", isWillSet, "isDidSet:", isDidSet