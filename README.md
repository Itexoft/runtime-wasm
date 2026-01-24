# runtime-wasm

NuGet package with prebuilt `dotnet.native*.wasm` variants for browser-wasm.

Contents are produced from the dotnet/runtime repository using Release flags plus:
- `WASM_SUPPORTS_DLOPEN=1`
- `-fPIC`
- `MAIN_MODULE=1/2`
- optional `WasmEnableThreads=true`

The package ships multiple files whose names encode the enabled flags.
