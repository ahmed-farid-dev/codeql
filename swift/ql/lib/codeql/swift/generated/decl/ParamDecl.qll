// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.decl.VarDecl

class ParamDeclBase extends Synth::TParamDecl, VarDecl {
  override string getAPrimaryQlClass() { result = "ParamDecl" }

  predicate isInout() { Synth::convertParamDeclToRaw(this).(Raw::ParamDecl).isInout() }
}