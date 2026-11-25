// Synthetic u8 x i8 dot probe. Only dot_evex may contain EVEX instructions.
// Each record is [block count, 8 LE u32 accumulators, activations, weights].
#include <cpuid.h>
#include <immintrin.h>
#include <cstdint>
#include <cstdio>
#include <cstring>

static bool admitted() {
    unsigned a, b, c, d, c1 = 0, b7 = 0, c7 = 0, xlo = 0, xhi = 0;
    if (__get_cpuid(1, &a, &b, &c, &d)) c1 = c;
    if (__get_cpuid_count(7, 0, &a, &b, &c, &d)) { b7 = b; c7 = c; }
    const unsigned avx_osxsave_xsave = 7u << 26;
    if ((c1 & avx_osxsave_xsave) == avx_osxsave_xsave)
        __asm__ volatile("xgetbv" : "=a"(xlo), "=d"(xhi) : "c"(0));
    std::fprintf(stderr, "cpuid_1_ecx=%08x cpuid_7_ebx=%08x cpuid_7_ecx=%08x xcr0=%08x%08x\n",
                 c1, b7, c7, xhi, xlo);
    const unsigned f_vl = (1u << 16) | (1u << 31);
    return (b7 & f_vl) == f_vl && (c7 & (1u << 11)) && (xlo & 0xe6u) == 0xe6u;
}

extern "C" __attribute__((noinline, target("avx512f,avx512vl,avx512vnni,no-avxvnni")))
void dot_evex(uint32_t *out, const uint8_t *a, const int8_t *w, int blocks) {
    __m256i acc = _mm256_loadu_si256(reinterpret_cast<const __m256i *>(out));
    for (int i = 0; i < blocks; ++i) {
        const auto v = _mm256_loadu_si256(reinterpret_cast<const __m256i *>(a + i*32));
        const auto k = _mm256_loadu_si256(reinterpret_cast<const __m256i *>(w + i*32));
        acc = _mm256_dpbusd_epi32(acc, v, k);
    }
    _mm256_storeu_si256(reinterpret_cast<__m256i *>(out), acc);
}

int main(int argc, char **argv) {
    if (argc != 2) return 2;
    const bool evex = !std::strcmp(argv[1], "evex");
    if (!evex && std::strcmp(argv[1], "scalar")) return 2;
    if (evex && !admitted()) return 77;
    uint32_t out[8]; uint8_t a[192]; int8_t w[192]; unsigned count = 0;
    for (int b; (b = std::fgetc(stdin)) != EOF;) {
        if ((b != 2 && b != 6) || ++count > 256) return 3;
        const auto len = static_cast<size_t>(32*b);
        if (std::fread(out, 1, sizeof(out), stdin) != sizeof(out) ||
            std::fread(a, 1, len, stdin) != len || std::fread(w, 1, len, stdin) != len) return 3;
        if (evex) dot_evex(out, a, w, b);
        else for (size_t k = 0; k < len; ++k) out[(k % 32)/4] += static_cast<uint32_t>(a[k]*w[k]);
        if (std::fwrite(out, 1, sizeof(out), stdout) != sizeof(out)) return 4;
    }
    return count && !std::ferror(stdin) && std::fflush(stdout) == 0 ? 0 : 3;
}
