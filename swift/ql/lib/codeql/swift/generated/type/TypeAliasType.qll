// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.type.SugarType
import codeql.swift.elements.decl.TypeAliasDecl

class TypeAliasTypeBase extends Synth::TTypeAliasType, SugarType {
  override string getAPrimaryQlClass() { result = "TypeAliasType" }

  TypeAliasDecl getImmediateDecl() {
    result =
      Synth::convertTypeAliasDeclFromRaw(Synth::convertTypeAliasTypeToRaw(this)
            .(Raw::TypeAliasType)
            .getDecl())
  }

  final TypeAliasDecl getDecl() { result = getImmediateDecl().resolve() }
}
