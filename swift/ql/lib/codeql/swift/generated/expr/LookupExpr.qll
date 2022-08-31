// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.decl.Decl
import codeql.swift.elements.expr.Expr

class LookupExprBase extends Synth::TLookupExpr, Expr {
  Expr getImmediateBase() {
    result =
      Synth::convertExprFromRaw(Synth::convertLookupExprToRaw(this).(Raw::LookupExpr).getBase())
  }

  final Expr getBase() { result = getImmediateBase().resolve() }

  Decl getImmediateMember() {
    result =
      Synth::convertDeclFromRaw(Synth::convertLookupExprToRaw(this).(Raw::LookupExpr).getMember())
  }

  final Decl getMember() { result = getImmediateMember().resolve() }

  final predicate hasMember() { exists(getMember()) }
}