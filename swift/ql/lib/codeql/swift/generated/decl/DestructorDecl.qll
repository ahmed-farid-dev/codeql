// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.decl.AbstractFunctionDecl

class DestructorDeclBase extends Synth::TDestructorDecl, AbstractFunctionDecl {
  override string getAPrimaryQlClass() { result = "DestructorDecl" }
}
