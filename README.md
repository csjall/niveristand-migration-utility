# SLSC System Definition Migration Utility

**SLSC System Definition Migration Utility** allows users to migrate VeriStand system definition files with SLSC configuration from version 2015/2016 to version 2017. The utility updates the system definition file by moving the SLSC chassis and module configuration under _Hardware/SLSC_ folder in System Explorer.

## Python Version

Python 3.6.x or later.

## Usage

```python.exe .\migrateSlscSystemDefinition.py <input_file> <output_file>```

where `<input_file>` is the existing VeriStand system definition file and `<output_file>` is the new migrated VeriStand definition file.

## Known Issues

When opening the newly migrated system definition file in VeriStand, an additonal SLSC folder appears under the Hardware folder in System Explorer. Remove the superfluous SLSC section by removing the following section from the system definition file.

```
<Section Name="SLSC" TypeGUID="3ea8ee87-daf4-4abc-a6e6-9c54a9452824">
   <Description />
   <Properties />
   <Errors />
</Section>
```

## License

The SLSC System Definition Migration Utility is licensed under an MIT-style license (see LICENSE). Other incorporated projects may be licensed under different licenses. All licenses allow for non-commercial and commercial use.