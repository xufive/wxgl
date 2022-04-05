---
sort: 1
---

# 颜色

WxGL支持十六进制的颜色、预定义的颜色，以及浮点型元组、列表或numpy数组表示的RGB/RGBA颜色。下面这些写法都是合法的。

* '#F3D6E9', '#de3f80'
* '#C6F', '#ab8'
* 'red', 'blue', 'cyan'
* (1.0, 0.8, 0.2), (1.0, 0.8, 0.2, 1.0)
* [1.0, 0.8, 0.2], [1.0, 0.8, 0.2, 1.0]
* numpy.array([1.0, 0.8, 0.2]), numpy.array([1.0, 0.8, 0.2, 1.0])

预定义的颜色共计148种。函数[wxgl.color_list](https://xufive.github.io/wxgl/api/util.html#wxglcolor_list)返回预定义的颜色列表，函数[wxgl.color_help](https://xufive.github.io/wxgl/api/util.html#wxglcolor_help)返回预定义的颜色中英文对照表。

* aliceblue              - 爱丽丝蓝
* antiquewhite           - 古董白
* aqua                   - 青
* aquamarine             - 碧绿
* azure                  - 青白
* beige                  - 米
* bisque                 - 橘黄
* black                  - 黑
* blanchedalmond         - 杏仁白
* blue                   - 蓝
* blueviolet             - 蓝紫
* brown                  - 褐
* burlywood              - 硬木褐
* cadetblue              - 军服蓝
* chartreuse             - 查特酒绿
* chocolate              - 巧克力
* coral                  - 珊瑚红
* cornflowerblue         - 矢车菊蓝
* cornsilk               - 玉米穗黄
* crimson                - 绯红
* cyan                   - 青
* darkblue               - 深蓝
* darkcyan               - 深青
* darkgoldenrod          - 深金菊黄
* darkgray               - 暗灰
* darkgreen              - 深绿
* darkgrey               - 暗灰
* darkkhaki              - 深卡其
* darkmagenta            - 深品红
* darkolivegreen         - 深橄榄绿
* darkorange             - 深橙
* darkorchid             - 深洋兰紫
* darkred                - 深红
* darksalmon             - 深鲑红
* darkseagreen           - 深海藻绿
* darkslateblue          - 深岩蓝
* darkslategray          - 深岩灰
* darkslategrey          - 深岩灰
* darkturquoise          - 深松石绿
* darkviolet             - 深紫
* deeppink               - 深粉
* deepskyblue            - 深天蓝
* dimgray                - 昏灰
* dimgrey                - 昏灰
* dodgerblue             - 湖蓝
* firebrick              - 火砖红
* floralwhite            - 花卉白
* forestgreen            - 森林绿
* fuchsia                - 洋红
* gainsboro              - 庚氏灰
* ghostwhite             - 幽灵白
* gold                   - 金
* goldenrod              - 金菊
* gray                   - 灰
* green                  - 绿
* greenyellow            - 黄绿
* grey                   - 灰
* honeydew               - 蜜瓜绿
* hotpink                - 艳粉
* indianred              - 印度红
* indigo                 - 靛蓝
* ivory                  - 象牙白
* khaki                  - 卡其
* lavender               - 薰衣草紫
* lavenderblush          - 薰衣草红
* lawngreen              - 草坪绿
* lemonchiffon           - 柠檬绸黄
* lightblue              - 浅蓝
* lightcoral             - 浅珊瑚红
* lightcyan              - 浅青
* lightgoldenrodyellow   - 浅金菊黄
* lightgray              - 亮灰
* lightgreen             - 浅绿
* lightgrey              - 亮灰
* lightpink              - 浅粉
* lightsalmon            - 浅鲑红
* lightseagreen          - 浅海藻绿
* lightskyblue           - 浅天蓝
* lightslategray         - 浅岩灰
* lightslategrey         - 浅岩灰
* lightsteelblue         - 浅钢青
* lightyellow            - 浅黄
* lime                   - 绿
* limegreen              - 青柠绿
* linen                  - 亚麻
* magenta                - 洋红
* maroon                 - 栗
* mediumaquamarine       - 中碧绿
* mediumblue             - 中蓝
* mediumorchid           - 中洋兰紫
* mediumpurple           - 中紫
* mediumseagreen         - 中海藻绿
* mediumslateblue        - 中岩蓝
* mediumspringgreen      - 中嫩绿
* mediumturquoise        - 中松石绿
* mediumvioletred        - 中紫红
* midnightblue           - 午夜蓝
* mintcream              - 薄荷乳白
* mistyrose              - 雾玫瑰红
* moccasin               - 鹿皮
* navajowhite            - 土著白
* navy                   - 藏青
* oldlace                - 旧蕾丝白
* olive                  - 橄榄
* olivedrab              - 橄榄绿
* orange                 - 橙
* orangered              - 橘红
* orchid                 - 洋兰紫
* palegoldenrod          - 白金菊黄
* palegreen              - 白绿
* paleturquoise          - 白松石绿
* palevioletred          - 白紫红
* papayawhip             - 番木瓜橙
* peachpuff              - 粉朴桃
* peru                   - 秘鲁红
* pink                   - 粉
* plum                   - 李紫
* powderblue             - 粉末蓝
* purple                 - 紫
* rebeccapurple          - 丽贝卡紫
* red                    - 红
* rosybrown              - 玫瑰褐
* royalblue              - 品蓝
* saddlebrown            - 鞍褐
* salmon                 - 鲑红
* sandybrown             - 沙褐
* seagreen               - 海藻绿
* seashell               - 贝壳白
* sienna                 - 土黄赭
* silver                 - 银
* skyblue                - 天蓝
* slateblue              - 岩蓝
* slategray              - 岩灰
* slategrey              - 岩灰
* snow                   - 雪白
* springgreen            - 春绿
* steelblue              - 钢青
* tan                    - 日晒褐
* teal                   - 鸭翅绿
* thistle                - 蓟紫
* tomato                 - 番茄红
* turquoise              - 松石绿
* violet                 - 紫罗兰
* wheat                  - 麦
* white                  - 白
* whitesmoke             - 烟雾白
* yellow                 - 黄
* yellowgreen            - 暗黄绿
