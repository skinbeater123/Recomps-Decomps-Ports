# Builds only the two TGP482 XboxXBERecomp host tools the Buffy probe needs (xbe_recomp, xbe_symbols),
# without the Windows D3D12/SDL3/ImGui runtime that cmake/XbeRecomp.cmake also pulls in.
# -DXBE_SDK=<XboxXBERecomp checkout>; pass FETCHCONTENT_SOURCE_DIR_ZYDIS / _TOMLPLUSPLUS to build offline.
cmake_minimum_required(VERSION 3.22)
project(buffy_recomp_host LANGUAGES C CXX)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if(NOT XBE_SDK)
    message(FATAL_ERROR "-DXBE_SDK=<path to TGP482/XboxXBERecomp> is required")
endif()
include(FetchContent)
set(ZYDIS_BUILD_TOOLS OFF CACHE BOOL "" FORCE)
set(ZYDIS_BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(ZYDIS_BUILD_DOXYGEN OFF CACHE BOOL "" FORCE)
# Same pins as XbeRecomp.cmake at TGP482 90bccea (v4.1.1 = a2278f1, v3.4.0 = 3017243)
FetchContent_Declare(zydis GIT_REPOSITORY https://github.com/zyantific/zydis.git GIT_TAG v4.1.1 GIT_SHALLOW TRUE)
FetchContent_Declare(tomlplusplus GIT_REPOSITORY https://github.com/marzer/tomlplusplus.git GIT_TAG v3.4.0 GIT_SHALLOW TRUE)
FetchContent_MakeAvailable(zydis tomlplusplus)

file(GLOB RECOMP_SOURCES ${XBE_SDK}/tools/recomp/*.cpp)
add_executable(xbe_recomp ${RECOMP_SOURCES})
target_include_directories(xbe_recomp PRIVATE ${XBE_SDK}/runtime ${XBE_SDK}/tools/recomp)
target_compile_definitions(xbe_recomp PRIVATE _CRT_SECURE_NO_WARNINGS)
target_link_libraries(xbe_recomp PRIVATE Zydis tomlplusplus::tomlplusplus)

add_executable(xbe_symbols ${XBE_SDK}/tools/symbols/main.cpp)
target_include_directories(xbe_symbols PRIVATE ${XBE_SDK}/runtime)
target_compile_definitions(xbe_symbols PRIVATE _CRT_SECURE_NO_WARNINGS)
target_link_libraries(xbe_symbols PRIVATE Zydis tomlplusplus::tomlplusplus)
