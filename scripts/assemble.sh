#!/bin/bash
set -e
rm -f list.txt
for i in $(seq 0 15); do echo "file 'parts/part-$i.mp4'" >> list.txt; done
ffmpeg -y -v error -f concat -safe 0 -i list.txt -c copy video.mp4
ffmpeg -y -v error \
 -i vo/01-coldopen.mp3 -i vo/02-act1-arrows.mp3 -i vo/03-act1-fertility.mp3 -i vo/04-act1-paradox.mp3 \
 -i vo/05-space-dive.mp3 -i vo/06-space-akiya.mp3 -i vo/07-time.mp3 -i vo/08-machine.mp3 \
 -i vo/09-blackhole.mp3 -i vo/10-bill.mp3 -i vo/11-economy.mp3 -i vo/12-finale-curve.mp3 \
 -i vo/13-finale-trying.mp3 -i vo/14-finale-korea.mp3 \
 -stream_loop -1 -t 424 -i audio/music-main.mp3 -i audio/music-dark.mp3 \
 -i audio/sfx-whoosh.wav -i audio/sfx-slam.wav -i audio/sfx-pop.wav -i audio/sfx-riser.wav \
 -filter_complex "\
[0]adelay=800:all=1[a0];\
[1]adelay=34900:all=1[a1];\
[2]adelay=60000:all=1[a2];\
[3]adelay=85200:all=1[a3];\
[4]adelay=106933:all=1[a4];\
[5]adelay=134667:all=1[a5];\
[6]adelay=162700:all=1[a6];\
[7]adelay=205033:all=1[a7];\
[8]adelay=256400:all=1[a8];\
[9]adelay=297567:all=1[a9];\
[10]adelay=336433:all=1[a10];\
[11]adelay=356267:all=1[a11];\
[12]adelay=386133:all=1[a12];\
[13]adelay=406333:all=1[a13];\
[a0][a1][a2][a3][a4][a5][a6][a7][a8][a9][a10][a11][a12][a13]amix=inputs=14:normalize=0:dropout_transition=0[vom];\
[vom]asplit=2[vomA][vomK];\
[14]atrim=0:423,volume=0.07,afade=t=in:d=1.5,afade=t=out:st=411:d=11[mm0];\
[15]atrim=0:97,afade=t=in:d=4,afade=t=out:st=89:d=8,volume=0.16,adelay=203500:all=1[md0];\
[mm0][md0]amix=inputs=2:normalize=0:dropout_transition=0[mus];\
[mus][vomK]sidechaincompress=threshold=0.012:ratio=10:attack=100:release=600[musD];\
[16]volume=0.5,asplit=11[w0][w1][w2][w3][w4][w5][w6][w7][w8][w9][w10];\
[w0]adelay=34100:all=1[W0];\
[w1]adelay=59767:all=1[W1];\
[w2]adelay=84400:all=1[W2];\
[w3]adelay=106133:all=1[W3];\
[w4]adelay=132800:all=1[W4];\
[w5]adelay=161900:all=1[W5];\
[w6]adelay=204233:all=1[W6];\
[w7]adelay=256233:all=1[W7];\
[w8]adelay=296767:all=1[W8];\
[w9]adelay=355467:all=1[W9];\
[w10]adelay=405800:all=1[W10];\
[17]volume=0.6,asplit=12[s0][s1][s2][s3][s4][s5][s6][s7][s8][s9][s10][s11];\
[s0]adelay=5000:all=1[S0];\
[s1]adelay=29333:all=1[S1];\
[s2]adelay=48433:all=1[S2];\
[s3]adelay=64767:all=1[S3];\
[s4]adelay=150133:all=1[S4];\
[s5]adelay=179567:all=1[S5];\
[s6]adelay=258233:all=1[S6];\
[s7]adelay=316767:all=1[S7];\
[s8]adelay=319433:all=1[S8];\
[s9]adelay=322767:all=1[S9];\
[s10]adelay=417800:all=1[S10];\
[s11]adelay=420467:all=1[S11];\
[18]volume=0.4,asplit=15[p0][p1][p2][p3][p4][p5][p6][p7][p8][p9][p10][p11][p12][p13][p14];\
[p0]adelay=18667:all=1[P0];\
[p1]adelay=21333:all=1[P1];\
[p2]adelay=41100:all=1[P2];\
[p3]adelay=73433:all=1[P3];\
[p4]adelay=91067:all=1[P4];\
[p5]adelay=92400:all=1[P5];\
[p6]adelay=99067:all=1[P6];\
[p7]adelay=124800:all=1[P7];\
[p8]adelay=145467:all=1[P8];\
[p9]adelay=180567:all=1[P9];\
[p10]adelay=260900:all=1[P10];\
[p11]adelay=337767:all=1[P11];\
[p12]adelay=339767:all=1[P12];\
[p13]adelay=340100:all=1[P13];\
[p14]adelay=412133:all=1[P14];\
[19]volume=0.45,asplit=2[r0][r1];\
[r0]adelay=263967:all=1[R0];\
[r1]adelay=404300:all=1[R1];\
[vomA][musD][W0][W1][W2][W3][W4][W5][W6][W7][W8][W9][W10][S0][S1][S2][S3][S4][S5][S6][S7][S8][S9][S10][S11][P0][P1][P2][P3][P4][P5][P6][P7][P8][P9][P10][P11][P12][P13][P14][R0][R1]amix=inputs=42:normalize=0:dropout_transition=0,alimiter=limit=0.95[aout]" \
 -map "[aout]" -c:a aac -b:a 192k mix.m4a
ffmpeg -y -v error -i video.mp4 -i mix.m4a -map 0:v -map 1:a -c:v copy -c:a copy -movflags +faststart -t 422.84 tokyo-full.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 tokyo-full.mp4
