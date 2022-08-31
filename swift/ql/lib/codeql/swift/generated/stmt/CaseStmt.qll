// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.stmt.CaseLabelItem
import codeql.swift.elements.stmt.Stmt
import codeql.swift.elements.decl.VarDecl

class CaseStmtBase extends Synth::TCaseStmt, Stmt {
  override string getAPrimaryQlClass() { result = "CaseStmt" }

  Stmt getImmediateBody() {
    result = Synth::convertStmtFromRaw(Synth::convertCaseStmtToRaw(this).(Raw::CaseStmt).getBody())
  }

  final Stmt getBody() { result = getImmediateBody().resolve() }

  CaseLabelItem getImmediateLabel(int index) {
    result =
      Synth::convertCaseLabelItemFromRaw(Synth::convertCaseStmtToRaw(this)
            .(Raw::CaseStmt)
            .getLabel(index))
  }

  final CaseLabelItem getLabel(int index) { result = getImmediateLabel(index).resolve() }

  final CaseLabelItem getALabel() { result = getLabel(_) }

  final int getNumberOfLabels() { result = count(getALabel()) }

  VarDecl getImmediateVariable(int index) {
    result =
      Synth::convertVarDeclFromRaw(Synth::convertCaseStmtToRaw(this)
            .(Raw::CaseStmt)
            .getVariable(index))
  }

  final VarDecl getVariable(int index) { result = getImmediateVariable(index).resolve() }

  final VarDecl getAVariable() { result = getVariable(_) }

  final int getNumberOfVariables() { result = count(getAVariable()) }
}