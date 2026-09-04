# PyHLSearch_Beam
HLSearchにビームサーチを適用した探索プログラム。

## 実行

```bat
python HLSearch_Beam.py --depth 10 --beam-width 100
```

`--beam-width` は各階層で残す候補数です。値が小さいほど高速になりますが、
探索対象を絞るため、完全探索とは結果が異なる場合があります。
