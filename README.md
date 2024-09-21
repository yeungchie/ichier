<h1 align="center"><span style="color:red"><u>I</u></span>ntegrated <span style="color:red"><u>C</u></span>ircuit <span style="color:red"><u>Hier</u></span>archy</h1>

## 做什么用？

> 懒得写，AI 帮我总结了一下。

`ichier` 是一个用于创建和处理电路设计的 Python 库。它允许用户定义设计、模块、端口和实例，并生成对应的代码。具体来说，这个库可以用于以下几个方面：

1. **设计创建**：通过 `Design` 和 `Module` 等类，可以构建电路设计，并添加多个模块来实现抽象的对应关系。
2. **终端和网络定义**：可以轻松定义模块之间的连接，通过设置输入输出端口 `Terminal` 和内部网络 `net` 来描述电路的交互。
3. **实例化模块**：允许将模块实例化多次，以便在设计中复用特定的功能，比如在一个电路中多次使用同一个逻辑门。

此库适合电子工程师用于快速创建和管理电子电路设计，特别是在较大规模的项目中，通过代码来描述设计结构可以提高效率和可维护性。

## 安装

```bash
pip install ichier -U
```

## 一个例子

```python
import json

from ichier import *


design = Design(
    modules=[
        Module(
            name="inv",
            terminals=[
                Terminal(name="A", direction="in"),
                Terminal(name="Z", direction="out"),
            ],
        ),
        Module(
            name="buf",
            terminals=[
                Terminal(
                    name="A",
                    direction="in",
                    net_name="A",
                ),
                Terminal(
                    name="Z",
                    direction="out",
                    net_name="Z",
                ),
            ],
            nets=[
                Net(name="A"),
                Net(name="Z"),
                Net(name="inter"),
            ],
            instances=[
                Instance(
                    name="i1",
                    reference="inv",
                    connection={
                        "A": "A",
                        "Z": "Z",
                    },
                    parameters={"size": "x2"},
                ),
                Instance(
                    name="i2",
                    reference="inv",
                    connection={
                        "A": "Z",
                        "Z": "A",
                    },
                    parameters={"size": "x4"},
                ),
            ],
        ),
    ],
)

print(json.dumps(design.summary(), indent=4))
```

+ 打印结果：

```json
{
    "name": "c334c842",
    "parameters": 0,
    "modules": {
        "total": 2,
        "list": [
            {
                "name": "inv",
                "instances": 0,
                "terminals": 2,
                "nets": 0,
                "parameters": 0
            },
            {
                "name": "buf",
                "instances": 2,
                "terminals": 2,
                "nets": 3,
                "parameters": 0
            }
        ]
    }
}
```
