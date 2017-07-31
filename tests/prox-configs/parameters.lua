--
-- Dataplane Automated Testing System
--
-- Copyright (c) 2015-2016, Intel Corporation.
-- All rights reserved.
--
-- Redistribution and use in source and binary forms, with or without
-- modification, are permitted provided that the following conditions
-- are met:
--
--   * Redistributions of source code must retain the above copyright
--     notice, this list of conditions and the following disclaimer.
--   * Redistributions in binary form must reproduce the above copyright
--     notice, this list of conditions and the following disclaimer in
--     the documentation and/or other materials provided with the
--     distribution.
--   * Neither the name of Intel Corporation nor the names of its
--     contributors may be used to endorse or promote products derived
--     from this software without specific prior written permission.
--
-- THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
-- "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
-- LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
-- A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
-- OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
-- SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
-- LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
-- DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
-- THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
-- (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
-- OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--

tester_mac0="00:00:00:00:00:01"
tester_mac1="00:00:00:00:00:02"
tester_mac2="00:00:00:00:00:03"
tester_mac3="00:00:00:00:00:04"
sut_mac0="00 00 00 00 00 01"
sut_mac1="00 00 00 00 00 02"
sut_mac2="00 00 00 00 00 03"
sut_mac3="00 00 00 00 00 04"

--qinq_tag="0xa888"
--qinq_tag_inline="88 a8"
qinq_tag="0x0081"
qinq_tag_inline="81 00"

tester_socket_id="0"
sut_socket_id="0"

tester_master="0s" .. tester_socket_id
tester_core1="1s" .. tester_socket_id
tester_core2="2s" .. tester_socket_id
tester_core3="3s" .. tester_socket_id
tester_core4="4s" .. tester_socket_id
tester_core5="5s" .. tester_socket_id
tester_core6="6s" .. tester_socket_id
tester_core7="7s" .. tester_socket_id
tester_core8="8s" .. tester_socket_id
tester_core9="9s" .. tester_socket_id
tester_core10="10s" .. tester_socket_id

tester_core1h="1s" .. tester_socket_id .. "h"
tester_core2h="2s" .. tester_socket_id .. "h"
tester_core3h="3s" .. tester_socket_id .. "h"
tester_core4h="4s" .. tester_socket_id .. "h"
tester_core5h="5s" .. tester_socket_id .. "h"
tester_core6h="6s" .. tester_socket_id .. "h"
tester_core7h="7s" .. tester_socket_id .. "h"
tester_core8h="8s" .. tester_socket_id .. "h"
tester_core9h="9s" .. tester_socket_id .. "h"
tester_core10h="10s" .. tester_socket_id .. "h"

sut_master="0s" .. sut_socket_id
sut_core1="1s" .. sut_socket_id
sut_core2="2s" .. sut_socket_id
sut_core3="3s" .. sut_socket_id
sut_core4="4s" .. sut_socket_id
sut_core5="5s" .. sut_socket_id
sut_core6="6s" .. sut_socket_id
sut_core7="7s" .. sut_socket_id
sut_core8="8s" .. sut_socket_id
sut_core9="9s" .. sut_socket_id
sut_core10="10s" .. sut_socket_id

sut_core1h="1s" .. sut_socket_id .. "h"
sut_core2h="2s" .. sut_socket_id .."h"
sut_core3h="3s" .. sut_socket_id .."h"
sut_core4h="4s" .. sut_socket_id .."h"
sut_core5h="5s" .. sut_socket_id .."h"
sut_core6h="6s" .. sut_socket_id .."h"
sut_core7h="7s" .. sut_socket_id .."h"
sut_core8h="8s" .. sut_socket_id .."h"
sut_core9h="9s" .. sut_socket_id .."h"
sut_core10h="10s" .. sut_socket_id .."h"

sut_bng_wk     = sut_core5 .. "-" .. sut_core8 .. "," .. sut_core5h .. "-" .. sut_core8h
sut_bng_qos_wk = sut_core7 .. "-" .. sut_core9 .. "," .. sut_core7h .. "-" .. sut_core9h
sut_vpe_wkd    = sut_core5 .. "-" .. sut_core6 .. "," .. sut_core5h .. "-" .. sut_core6h
sut_vpe_wku    = sut_core7 .. "-" .. sut_core9 .. "," .. sut_core7h .. "-" .. sut_core9h

