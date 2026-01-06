# _libremidi nanobind extension module
nanobind_add_module(_libremidi aldakit/_libremidi.cpp)
target_link_libraries(_libremidi PUBLIC libremidi)

set_target_properties(_libremidi PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/aldakit"
    ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/aldakit"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/aldakit"
)

# Install directive for scikit-build-core
install(TARGETS _libremidi LIBRARY DESTINATION aldakit)

# _tsf nanobind extension module (TinySoundFont + miniaudio)
nanobind_add_module(_tsf aldakit/_tsf.cpp)
target_include_directories(_tsf PRIVATE
    ${CMAKE_SOURCE_DIR}/thirdparty/TinySoundFont
    ${CMAKE_SOURCE_DIR}/thirdparty/miniaudio
)

# Platform-specific audio frameworks
if(APPLE)
    target_link_libraries(_tsf PRIVATE
        "-framework CoreFoundation"
        "-framework CoreAudio"
        "-framework AudioToolbox"
    )
elseif(UNIX AND NOT APPLE)
    # Linux: link pthread, dl, m (miniaudio needs these)
    target_link_libraries(_tsf PRIVATE pthread dl m)
elseif(WIN32)
    # Windows: no extra libs needed, miniaudio uses COM
endif()

set_target_properties(_tsf PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/aldakit"
    ARCHIVE_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/aldakit"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_SOURCE_DIR}/src/aldakit"
)

install(TARGETS _tsf LIBRARY DESTINATION aldakit)
