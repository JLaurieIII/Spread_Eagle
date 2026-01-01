{% macro generate_schema_name(custom_schema_name, node) -%}
    {#
        Custom schema naming macro.
        
        Default dbt behavior: {{ target.schema }}_{{ custom_schema_name }}
        Our behavior: Use {{ custom_schema_name }} directly
        
        This gives us clean, scalable schema names:
        - staging_cfb, staging_cbb, staging_nfl, etc.
        - intermediate_cfb, intermediate_cbb, etc.
        - marts_cfb, marts_cbb, etc.
        
        To add a new sport, just add it to dbt_project.yml:
            staging:
              new_sport:
                +schema: staging_new_sport
    #}
    
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
