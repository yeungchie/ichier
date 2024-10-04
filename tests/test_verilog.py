verilog_code = """
/*
  Library - TEST, Cell - TOP, View - schematic
  LAST TIME SAVED: Sep 12 21:45:51 2024
  NETLIST TIME: Sep 12 21:53:57 2024
 */

`timescale 1ns / 1ns 

(* flags = "place_not_replace" *)module TOP ( DQ, VREF, EXVPP, VDD, VSS, TM_17_L, TM_EXVPP_PWD,
     TM_VREF_PWD, TRIM_VPPOSC, XA, XCEb, XDIN, XERASEB, XERS_ALLb,
     XREADB, XWRITEB );

output  VREF;

inout  EXVPP, VDD, VSS;

input  TM_17_L, TM_EXVPP_PWD, TM_VREF_PWD, XCEb, XERASEB, XERS_ALLb,
     XREADB, XWRITEB;

output [0:7]  DQ;

input [0:1]  TRIM_VPPOSC;
input [0:7]  XDIN;
input [0:1]  XA;


specify 
    specparam CDS_LIBNAME  = "TEST";
    specparam CDS_CELLNAME = "TOP";
    specparam CDS_VIEWNAME = "schematic";
endspecify

E2TK2G I0 ( .XA(XA[0:1]), .VSS(VSS), .EXVPP(EXVPP), .VDD(VDD),
     .DQ(DQ[0:7]), .VREF(VREF), .TM_17_L(TM_17_L),
     .TM_EXVPP_PWD(TM_EXVPP_PWD), .TM_VREF_PWD(TM_VREF_PWD),
     .TRIM_VPPOSC(TRIM_VPPOSC[0:1]), .XCEb(XCEb), .XDIN(XDIN[0:7]),
     .XERASEB(XERASEB), .XERS_ALLb(XERS_ALLb), .XREADB(XREADB),
     .XWRITEB(XWRITEB));

endmodule


// End HDL models
"""

from ichier.parser.verilog import VerilogLexer
from ichier.parser import fromVerilog


class TestVerilogParser:
    def test_lexer(self):
        with open("tmp/netlist/test.v") as f:
            # with open("tmp/netlist/cds_alias.v") as f:
            # with open("tmp/netlist/802.11n.va") as f:
            data = f.read()
        # data = verilog_code
        lexer = VerilogLexer(data)
        print(lexer)
        for token in list(lexer):
            print(token)


# with open("tmp/netlist/top.v") as f:
#     data = f.read()

# import IPython

# IPython.start_ipython(
#     user_ns={
#         "verilog_code": verilog_code,
#         "lexer": lexer,
#         # "tokens": tokens,
#     }
# )


if __name__ == "__main__":
    import IPython

    de = fromVerilog("tmp/netlist/encoder.v")
    IPython.start_ipython(
        user_ns={
            "de": de,
        }
    )
