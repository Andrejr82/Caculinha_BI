import pyarrow as pa

# Testar PyArrow Table
t = pa.table({'a': [1,2,3]})
print(f'Type: {type(t)}')
print(f'Has __len__: {hasattr(t, "__len__")}')
print(f'Len: {len(t)}')
