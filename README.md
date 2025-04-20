<h1 align="center"><span style="color:red"><u>I</u></span>ntegrated <span style="color:red"><u>C</u></span>ircuit <span style="color:red"><u>Hier</u></span>archy</h1>

!["PyPI"](https://img.shields.io/pypi/v/ichier) !["PyPI"](https://img.shields.io/pypi/format/ichier) !["PyPI"](https://img.shields.io/pypi/pyversions/ichier) !["PyPI"](https://img.shields.io/pypi/dm/ichier) !["PyPI"](https://img.shields.io/pypi/l/ichier)

## 做什么用？

> 懒得写，AI 帮我总结了一下。

`ichier` 是一个用于创建和处理电路设计的 Python 库。它允许用户定义设计、模块、端口和实例，并生成对应的代码。这个库可以用于以下几个方面：

1. **设计创建**：通过 `Design` 和 `Module` 等类，可以构建电路设计，并添加多个模块来实现抽象的对应关系。
2. **终端和网络定义**：可以轻松定义模块之间的连接，通过设置输入输出端口 `Terminal` 和内部网络 `net` 来描述电路的交互。
3. **实例化模块**：允许将模块实例化多次，以便在设计中复用特定的功能，比如在一个电路中多次使用同一个逻辑门。

4. **代码解析**：支持解析 Spice 和 Verilog 格式的电路文件，生成 `Design` 对象，方便分析电路结构和参数，提取设计信息。
5. **命令行交互**：支持在 Python 中启动交互式 shell，方便对电路的信息进行查询。

## 安装

```bash
pip install ichier[full]
```

> 为了更好的使用体验，请指定 `[full]` 进行安装，否则将不会安装 `ipython` 和 `rich` 库。

## 描述一个电路

> buffer.py

```python
from ichier import *

design = Design(
    modules=[
        Module("inv", [Terminal("A", "input"), Terminal("Z", "output")]),
        Module(
            name="buf",
            terminals=[Terminal("A", "input"), Terminal("Z", "output")],
            nets=[Net("A"), Net("Z"), Net("inter")],
            instances=[
                Instance(
                    "inv", "i1", {"A": "A", "Z": "inter"}, {"size": "x2"}
                ),
                Instance(
                    reference="inv",
                    name="i2",
                    connection={"A": "inter", "Z": "Z"},
                    parameters={"size": "x4"},
                ),
            ],
        ),
    ],
)
```

+ 查询信息

```python
design.modules.figs
# => (Module('inv'), Module('buf'))

buf = design.modules["buf"]

buf.terminals.figs
# => (Terminal('A', 'input'), Terminal('Z', 'output'))

buf.instances.figs
# => (Instance('i1'), Instance('i2'))

buf.nets.figs
# => (Net('A'), Net('Z'), Net('inter'))
```

+ 导出为 Spice

```python
print(design.dumpToSpice())
```

```spice
.SUBCKT inv A Z
*.PININFO A:I Z:O
.ENDS


.SUBCKT buf A Z
*.PININFO A:I Z:O
Xi1 A inter inv size=x2
Xi2 inter Z inv size=x4
.ENDS
```

## 从网表读入设计

```spice
* top.cdl

.SUBCKT inv A Z
*.PININFO A:I Z:O
.ENDS

.SUBCKT buf A Z
*.PININFO A:I Z:O
Xi1 / inv $PINS A=A Z=inter
Xi2 / inv $PINS A=inter Z=Z
.ENDS
```

+ 解析 Spice 文件

```python
from ichier import fromSpice
design = fromSpice("top.cdl", rebuild=True)
```

+ 解析 Verilog 文件

```verilog
// top.v

module inv ( input A, output Z );
endmodule

module buf ( input A, output Z );
wire inter;
inv i1 (.A(A), .Z(inter));
inv i2 (.A(inter), .Z(Z));
endmodule
```

```python
from ichier import fromVerilog
design = fromVerilog("top.v", rebuild=True)
```

+ 也可以直接使用 CLI 工具

```shell
ichier parse top.v
ichier parse top.cdl
```

> 建议预先安装 `ipython` 和 `rich` 库，会有更好的交互体验。

![parse](./img/parse.gif "Parse")

## LICENSE

GNU Affero General Public License v3
