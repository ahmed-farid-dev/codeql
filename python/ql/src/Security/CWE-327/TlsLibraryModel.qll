import python
import semmle.python.ApiGraphs
import Ssl
import PyOpenSSL

/**
 * A specific protocol version.
 * We use this to identify a protocol.
 */
class ProtocolVersion extends string {
  ProtocolVersion() { this in ["SSLv2", "SSLv3", "TLSv1", "TLSv1_1", "TLSv1_2", "TLSv1_3"] }

  predicate lessThan(ProtocolVersion version) {
    this = "SSLv2" and version = "SSLv3"
    or
    this = "TLSv1" and version = ["TLSv1_1", "TLSv1_2", "TLSv1_3"]
    or
    this = ["TLSv1", "TLSv1_1"] and version = ["TLSv1_2", "TLSv1_3"]
    or
    this = ["TLSv1", "TLSv1_1", "TLSv1_2"] and version = "TLSv1_3"
  }

  predicate isInsecure() { this in ["SSLv2", "SSLv3", "TLSv1", "TLSv1_1"] }
}

/** An unspecific protocol version */
class ProtocolFamily extends string {
  ProtocolFamily() { this in ["SSLv23", "TLS"] }
}

/** The creation of a context. */
abstract class ContextCreation extends DataFlow::CfgNode {
  /** Gets the requested protocol if any. */
  abstract DataFlow::CfgNode getProtocol();
}

/** The creation of a connection from a context. */
abstract class ConnectionCreation extends DataFlow::CfgNode {
  /** Gets the context used to create the connection. */
  abstract DataFlow::CfgNode getContext();
}

/** A context is being restricted on which protocols it can accepts. */
abstract class ProtocolRestriction extends DataFlow::CfgNode {
  /** Gets the context being restricted. */
  abstract DataFlow::CfgNode getContext();

  /** Gets the protocol version being disallowed. */
  abstract ProtocolVersion getRestriction();
}

/** A context is being relaxed on which protocols it can accepts. */
abstract class ProtocolUnrestriction extends DataFlow::CfgNode {
  /** Gets the context being relaxed. */
  abstract DataFlow::CfgNode getContext();

  /** Gets the protocol version being allowed. */
  abstract ProtocolVersion getUnrestriction();
}

abstract class UnspecificContextCreation extends ContextCreation, ProtocolUnrestriction {
  TlsLibrary library;
  ProtocolFamily family;

  UnspecificContextCreation() { this.getProtocol() = library.unspecific_version(family) }

  override DataFlow::CfgNode getContext() { result = this }

  override ProtocolVersion getUnrestriction() {
    family = "TLS" and
    result in ["TLSv1", "TLSv1_1", "TLSv1_2", "TLSv1_3"]
    or
    // This can negotiate a TLS 1.3 connection (!)
    // see https://docs.python.org/3/library/ssl.html#ssl-contexts
    family = "SSLv23" and
    result in ["SSLv2", "SSLv3", "TLSv1", "TLSv1_1", "TLSv1_2", "TLSv1_3"]
  }
}

abstract class TlsLibrary extends string {
  TlsLibrary() { this in ["ssl", "pyOpenSSL"] }

  /** The name of a specific protocol version, known to be insecure. */
  abstract string specific_insecure_version_name(ProtocolVersion version);

  /** The name of an unspecific protocol version, say TLS, known to have insecure instances. */
  abstract string unspecific_version_name(ProtocolFamily family);

  /** The module or class holding the version constants. */
  abstract API::Node version_constants();

  /** A dataflow node representing a specific protocol version, known to be insecure. */
  DataFlow::Node insecure_version(ProtocolVersion version) {
    result = version_constants().getMember(specific_insecure_version_name(version)).getAUse()
  }

  /** A dataflow node representing an unspecific protocol version, say TLS, known to have insecure instances. */
  DataFlow::Node unspecific_version(ProtocolFamily family) {
    result = version_constants().getMember(unspecific_version_name(family)).getAUse()
  }

  /** The creation of a context with a deafult protocol. */
  abstract ContextCreation default_context_creation();

  /** The creation of a context with a specific protocol. */
  abstract ContextCreation specific_context_creation();

  /** The creation of a context with a specific protocol version, known to be insecure. */
  ContextCreation insecure_context_creation(ProtocolVersion version) {
    result = specific_context_creation() and
    result.getProtocol() = insecure_version(version)
  }

  /** The creation of a context with an unspecific protocol version, say TLS, known to have insecure instances. */
  DataFlow::CfgNode unspecific_context_creation(ProtocolFamily family) {
    result = default_context_creation()
    or
    result = specific_context_creation() and
    result.(ContextCreation).getProtocol() = unspecific_version(family)
  }

  /** A connection is created in an insecure manner, not from a context. */
  abstract DataFlow::CfgNode insecure_connection_creation(ProtocolVersion version);

  /** A connection is created from a context. */
  abstract ConnectionCreation connection_creation();

  /** A context is being restricted on which protocols it can accepts. */
  abstract ProtocolRestriction protocol_restriction();

  /** A context is being relaxed on which protocols it can accepts. */
  abstract ProtocolUnrestriction protocol_unrestriction();
}
