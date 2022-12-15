#pragma once

#include <array>

namespace codeql {
constexpr std::array swiftBuiltins = {
    "zeroInitializer",
    "BridgeObject",
    "Word",
    "NativeObject",
    "RawPointer",
    "Executor",
    "Job",
    "RawUnsafeContinuation",
    "addressof",
    "initialize",
    "reinterpretCast",
    "Int1",
    "Int8",
    "Int16",
    "Int32",
    "Int64",
    "IntLiteral",
    "FPIEEE16",
    "FPIEEE32",
    "FPIEEE64",
    "FPIEEE80",
    "Vec2xInt8",
    "Vec4xInt8",
    "Vec8xInt8",
    "Vec16xInt8",
    "Vec32xInt8",
    "Vec64xInt8",
    "Vec2xInt16",
    "Vec4xInt16",
    "Vec8xInt16",
    "Vec16xInt16",
    "Vec32xInt16",
    "Vec64xInt16",
    "Vec2xInt32",
    "Vec4xInt32",
    "Vec8xInt32",
    "Vec16xInt32",
    "Vec32xInt32",
    "Vec64xInt32",
    "Vec2xInt64",
    "Vec4xInt64",
    "Vec8xInt64",
    "Vec16xInt64",
    "Vec32xInt64",
    "Vec64xInt64",
    "Vec2xFPIEEE16",
    "Vec4xFPIEEE16",
    "Vec8xFPIEEE16",
    "Vec16xFPIEEE16",
    "Vec32xFPIEEE16",
    "Vec64xFPIEEE16",
    "Vec2xFPIEEE32",
    "Vec4xFPIEEE32",
    "Vec8xFPIEEE32",
    "Vec16xFPIEEE32",
    "Vec32xFPIEEE32",
    "Vec64xFPIEEE32",
    "Vec2xFPIEEE64",
    "Vec4xFPIEEE64",
    "Vec8xFPIEEE64",
    "Vec16xFPIEEE64",
    "Vec32xFPIEEE64",
    "Vec64xFPIEEE64",

    "buildDefaultActorExecutorRef",
    "buildMainActorExecutorRef",
};
}
