// generated by codegen/codegen.py
private import codeql.swift.generated.Synth
private import codeql.swift.generated.Raw
import codeql.swift.elements.type.Type

class LValueTypeBase extends Synth::TLValueType, Type {
  override string getAPrimaryQlClass() { result = "LValueType" }

  Type getImmediateObjectType() {
    result =
      Synth::convertTypeFromRaw(Synth::convertLValueTypeToRaw(this)
            .(Raw::LValueType)
            .getObjectType())
  }

  final Type getObjectType() { result = getImmediateObjectType().resolve() }
}
