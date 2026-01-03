# TODO

## Future Features

### MIDI Input Support
Add MIDI input functionality to translate incoming MIDI messages to Alda syntax. This would enable:
- Real-time transcription from MIDI keyboards
- Recording MIDI performances as Alda code
- Interactive composition workflows

Reference: The original comprehensive libremidi Python bindings are available at `thirdparty/libremidi/bindings/python/` and include `MidiIn` support with polling wrappers.

### Conditional Full Bindings
The current `_libremidi` extension is minimal (output-only). Could add conditional build logic to detect optional dependencies and build full bindings when available:

- Check for `boost` and `readerwriterqueue` availability in CMake
- On macOS: `brew install boost readerwriterqueue`
- Define `LIBREMIDI_FULL_BINDINGS` preprocessor macro when deps found
- Use `#ifdef` in `_libremidi.cpp` to conditionally compile full vs minimal bindings

This would give users the option to install deps for advanced features (polling wrappers, MIDI input) while keeping zero-dependency builds working.
