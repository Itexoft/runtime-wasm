# runtime-wasm

Single NuGet package with prebuilt browser-wasm runtime variants from dotnet/runtime.

## Contents
- Native runtime variants: singlethread/multithread × mm1/mm2
- Managed runtime libraries for browser-wasm (net10.0)
- JS glue, ICU data, and native libs needed by the runtime

## Package layout
The package is merged into a single layout:

```
runtimes/
  browser-wasm/
    native/
      singlethread/
        mm1/
        mm2/
      multithread/
        mm1/
        mm2/
    lib/
      net10.0/
```

For the exact file list, see `NUGet-merged-structure.md`.

## Build notes
Built from dotnet/runtime (Release) with:
- `WASM_SUPPORTS_DLOPEN=1`
- `-fPIC`
- `MAIN_MODULE=1/2`
- `WasmEnableThreads=true` for multithread variants
