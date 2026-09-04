# PyHLSearch_Beam
HLSearchの素数シフト探索にビームサーチを適用したPythonプログラムです。
`HLSearch_Beam.py` は、import可能なモジュールとコマンドラインプログラムを兼ねています。

## 必要環境

- Python 3.13以降
- NumPy
- tqdm
- CUDAを使う場合: CUDA Toolkitに対応したCuPy

CPU版の依存パッケージをインストールします。

```bat
python -m pip install numpy tqdm
```

CUDA版を使う場合は、CUDA Toolkitのバージョンに合うCuPyを追加します。
たとえばCUDA 12.xでは次のようにインストールします。

```bat
python -m pip install cupy-cuda12x
```

CUDA 11.xなど別のバージョンを使用する場合は、CuPy公式の対応表に
従ってパッケージ名を選択してください。

## 基本実行

```bat
python HLSearch_Beam.py --depth 10 --beam-width 100
```

主なオプション:

| オプション | 説明 |
| --- | --- |
| `--depth N` | 探索する階層数 |
| `--beam-width N` | 各階層から次へ渡す候補数 |
| `--limit N` | 枝刈りする残存数の下限 |
| `--max-depth N` | `--target`による追加条件を有効にする深さ |
| `--target N` | 対象とする残存数 |
| `--primes-count N` | 使用する素数の個数 |
| `--cols N` | 探索対象の列数 |
| `--output PATH` | シフト経路の出力先 |
| `--checkpoint PATH` | 探索途中のチェックポイント保存先 |
| `--resume PATH` | 保存済みチェックポイントから再開 |
| `--backend {cpu,cuda}` | 探索バックエンド（既定値: `cpu`）。`cuda`はCuPyが必要 |
| `--benchmark` | 小規模CPUベンチマークを実行して終了 |
| `--benchmark-repeats N` | CPUベンチマークの反復回数 |

小規模な動作確認:

```bat
python HLSearch_Beam.py --depth 2 --primes-count 2 --cols 6 ^
  --limit 0 --max-depth 2 --target 2 --beam-width 6
```

## 出力

`--output`で指定したファイルには、次の形式で結果が保存されます。

```text
max_count:...
results:...
[shift0, shift1, ...]
```

ログはコンソールと`HLSearch_Beam.log`に出力されます。チェックポイントを指定すると、
探索状態をJSON形式で保存できます。保存中の異常終了で既存ファイルを壊さないよう、
一時ファイル経由で置き換えます。

## 探索と高速化

各階層で候補を評価し、残存数の多い上位候補だけを次の階層へ渡します。
`--beam-width`が小さいほど高速になりますが、探索対象が絞られるため、
完全探索とは異なる結果になる場合があります。最適解の完全性が必要な場合は、
ビーム幅と枝刈り条件の影響を考慮してください。

探索処理では次の最適化を使用しています。

- マスクを`uint64`へビットパックし、メモリ使用量を削減
- 候補シフトを一括AND・popcountで評価
- 上位ビーム候補の選択に`argpartition`を使用
- シフトテーブルをNumPyで一括生成
- 進捗表示とチェックポイント判定の頻度を抑制

`--backend cuda`を指定すると、シフトテーブルをGPUへ転送し、候補のAND演算と
popcountをCuPyでバッチ処理します。ビームの並べ替えやチェックポイントの
シリアライズはCPU側で行います。CUDA対応GPUまたは対応するCuPyが利用できない
環境では実行できません。

```bat
python HLSearch_Beam.py --backend cuda --depth 10 --beam-width 100
```

CPU性能を測定するには、検索と同じCLIから小規模ベンチマークを実行できます。
ベンチマークは常にCPUバックエンドで実行され、結果はJSONで標準出力に表示されます。
`elapsed_seconds`は全反復の合計時間、`nodes_per_second`は全反復の平均処理速度です。

```bat
python HLSearch_Beam.py --benchmark --depth 6 --primes-count 6 ^
  --cols 1024 --beam-width 64 --benchmark-repeats 3
```

## テスト

```bat
python -m pytest
```
