import os
import ast
import yaml



class Class:
    def __init__(self, c):
        self.class_def: ast.ClassDef = c
        self.name = c.name
        self.parents = [n.id if isinstance(n, ast.Name) else n.attr for n in c.bases]
        self.methods = [n.name for n in c.body if isinstance(n, ast.FunctionDef)]
        self.expression = self._get_expression()
        self.assigns = self._get_assigns()

    def _or_elements(self, left: ast.BinOp | ast.Name, right: ast.BinOp | ast.Name):
        result = ''
        if isinstance(left, ast.BinOp):
            result += self._or_elements(left=left.left, right=left.right)
        else:
            result += f'{left.id} | '

        if isinstance(right, ast.BinOp):
            result += self._or_elements(left=right.left, right=right.right)
        else:
            result += f' {right.id} |'
        return result

    def _get_assigns(self) -> dict:
        assigns = dict()
        for n in self.class_def.body:
            match n:
                case ast.Assign(value=ast.List(elements)):
                    match elements:
                        # We assume all the BinOp's operator is BitOr()
                        case [ast.BinOp(left=left, right=right), *names] | [*names, ast.BinOp(left=left, right=right)]:
                            # ex (Name): permission_classes = [PersonPermission, PersonPermission2 | PersonPermission3]
                            # ex (Attribute): permission_classes = [permissions.Permission, Permission2 | Permission3]
                            values = [n.value.id if isinstance(n, ast.Attribute) else n.id for n in names]
                            values.extend([self._or_elements(left=left, right=right)[:-2]])
                        case _:
                            values = list()
                            for v in n.value.elts:
                                match v:
                                    case ast.Tuple(ast.Name(id=val), ast.Call()):
                                        # ex: filter_backends = (DjangoFilterBackend, SearchFilter)
                                        pass
                                    case ast.Tuple(elts=[ast.Name(id=val), *_]):
                                        pass
                                    case ast.Tuple(ast.Constant(value=val)):
                                        pass
                                    case ast.Constant(value=val):
                                        # ex: store_field_name = 'blog__store'
                                        pass
                                    case ast.Name(id=val):
                                        # ex: permission_classes = [IsAuthenticated, IsBrandManager]
                                        pass
                                    case ast.Tuple(elts=[ast.Constant(value=val), *_]):
                                        pass
                                    case ast.Attribute(value=val):
                                        pass
                                    case _type:
                                        # print(f'{_type} Not Supported. (line: {_type.lineno})')
                                        continue
                                values.append(val)
                case ast.Assign(value=ast.Constant(value=_value)):
                    values = _value
                case ast.Assign(value=ast.Attribute(value=ast.Attribute(value=ast.Name(id=_value)))):
                    values = [_value]
                case ast.Assign(value=ast.Attribute(value=ast.Name(id=_value))):
                    values = [_value]
                case ast.Assign(value=ast.Name(id=_value)):
                    values = _value

                # Handling Model Fields
                case ast.Assign(
                    targets=[ast.Name(id=name)],
                    value=ast.Call(func=ast.Attribute(value=ast.Name(id=models), attr=field), keywords=[*keywords])
                ):
                    # ex: name = models.CharField(max_length=64)
                    _keywords = ''
                    for key in keywords:
                        match key.value:
                            case ast.Call(args=[ast.Constant(value=value)]):
                                # ex: verbose_name = _("description")
                                pass
                            case ast.Constant(value=value):
                                # ex: default=0
                                pass
                            case ast.Attribute(value=ast.Name(id=_val1), attr=_val2):
                                # ex: on_delete=models.PROTECT
                                value = f'{_val1}.{_val2}'
                            case ast.Name(id=value):
                                # ex: choices=VISIBILITY_TYPE
                                pass
                            case _type:
                                # print(f'{_type} Not Supported. (line: {_type.lineno})')
                                continue
                        _keywords += f'{key.arg}={value} '
                    values = f'{field}: {_keywords}'

                case ast.Expr():
                    # We handle it in self._get_expression() so continue
                    continue
                case _type:
                    # print(ast.dump(_type, indent=4))
                    # print(f'{_type} Not Supported. (line: {_type.lineno})')
                    continue

            key = n.targets[0].value.id if isinstance(n.targets[0], ast.Attribute) else n.targets[0].id
            assigns[key] = values
        return assigns

    def _get_expression(self) -> str:
        expression = ''
        for n in self.class_def.body:
            if isinstance(n, ast.Expr):
                expression += '\n'.join([s.strip() for s in n.value.value.split('\n')])

        return expression

    @property
    def permission_classes(self):
        return self.assigns.get('permission_classes')

    @property
    def queryset_model(self):
        return self.assigns.get('queryset')

    @property
    def serializer_class(self):
        return self.assigns.get('serializer_class')

    @property
    def pagination_class(self):
        return self.assigns.get('pagination_class')

    def __str__(self):
        return f'Class(name={self.name})'

    __repr__ = __str__


class Parse:
    def __init__(self, path: str):
        self.path = path

        with open(self.path, 'r') as f:
            self.node = ast.parse(f.read())
        self.functions = self._get_functions()
        self.classes = [Class(c) for c in self._get_classes()]

    def _get_functions(self):
        return [n for n in self.node.body if isinstance(n, ast.FunctionDef)]

    def _get_classes(self):
        return [n for n in self.node.body if isinstance(n, ast.ClassDef)]

    def __str__(self):
        return f"Parse('{self.path}')"

    __repr__ = __str__


class MakeDocstring:
    def __init__(self, file_path: str, base_directory: str, repo_url: str):
        self.base_directory = base_directory
        self.file_path = file_path
        self.repo_url = repo_url
        self.parsed_file = Parse(file_path)
        self.make_docstring()
        self.write_doc()

    @classmethod
    def expression_docs(cls, c):
        if c.expression:
            return f'{c.expression}\n'

    @classmethod
    def permissions_docs(cls, c):
        if permissions := c.permission_classes:
            return f'\n**Permissions:**`{permissions}`\n'

    @classmethod
    def serializers_docs(cls, c):
        if serializers := c.serializer_class:
            return f'\n**Serializers:**`{serializers}`\n'

    @classmethod
    def pagination_docs(cls, c):
        if pagination := c.pagination_class:
            return f'\n**Paginations:**`{pagination}`\n'

    @classmethod
    def assigns_docs(cls, c):
        # We should handle model fields here
        return '\n\n'.join(f'`{k}` --> {v}' for k, v in c.assigns.items())

    @classmethod
    def models_docs(cls, c):
        # TODO: Model (Queryset)
        if c.queryset_model:
            return f'\n**Model:**`{c.queryset_model}`\n'

    @classmethod
    def methods_docs(cls, c):
        docstring_body_method = ''
        for parent in c.parents:
            for p in parent.split('.'):
                # TODO: Handle All Of Classes (Serializer, ModelSerializer, APITestCase, ...)
                # TODO: Complete Methods Docs
                match p:
                    case 'ModelViewSet':
                        docstring_body_method += f'- Create\n- Retrieve\n- Update\n- List\n- Destroy'

                    case 'ReadOnlyModelViewSet':
                        docstring_body_method += f'- Retrieve\n- List'

                    case 'ListCreateAPIView':
                        docstring_body_method += f'- Create\n- List'

                    case 'RetrieveUpdateAPIView':
                        docstring_body_method += f'- Retrieve\n- Update'

                    case 'RetrieveUpdateDestroyAPIView':
                        docstring_body_method += f'- Retrieve\n- Update\n- Destroy'

                    case 'RetrieveDestroyAPIView':
                        docstring_body_method += f'- Retrieve\n- Destroy'

                    case 'CreateModelMixin' | 'CreateAPIView':
                        docstring_body_method += f'- Create\n'

                    case 'RetrieveModelMixin' | 'RetrieveAPIView':
                        docstring_body_method += f'- Retrieve\n'

                    case 'ListModelMixin' | 'ListAPIView':
                        docstring_body_method += f'- List\n'

                    case 'UpdateModelMixin' | 'UpdateAPIView':
                        docstring_body_method += f'- Update\n'

                    case 'DestroyModelMixin' | 'DestroyAPIView':
                        docstring_body_method += f'- Destroy\n'
        if docstring_body_method:
            return f'\n**Methods:**\n\n{docstring_body_method}\n'

    def make_docstring(self):
        self.docstring = ''
        for c in self.parsed_file.classes:
            docstring_body = self.expression_docs(c) or ''
            docstring_body += self.permissions_docs(c) or ''
            docstring_body += self.serializers_docs(c) or ''
            docstring_body += self.pagination_docs(c) or ''
            docstring_body += self.models_docs(c) or ''
            docstring_body += self.methods_docs(c) or ''
            docstring_body += self.assigns_docs(c) or ''

            # Body
            if docstring_body:
                rel_path = self.file_path.replace(self.base_directory, '')
                url = f'{self.repo_url}{rel_path}#L{c.class_def.lineno}'
                class_name = f'## [{c.name}]({url})\n\n'
                self.docstring += class_name + docstring_body + '\n\n'
        return self.docstring

    def write_doc(self):
        path = 'docs/'
        for _path in self.file_path.split('/'):
            if _path.endswith('.py'):
                continue
            if _path != self.base_directory:
                path += f'{_path}/'

        if self.docstring:
            if not os.path.exists(path):
                os.makedirs(path)
            file_name = self.file_path[self.file_path.rfind('/') + 1:self.file_path.rfind('.')]
            path += f'{file_name}.md'
            with open(path, 'w') as f:
                f.write(self.docstring)


def find_files(path: str):
    """path always should end with slash /"""
    files = list()
    for _path in os.listdir(path):
        full_path = path + _path
        if os.path.isdir(full_path):
            # TODO: Maybe we can create .docsignore or something like that
            if _path in ['migrations', '__pycache__', '.venv']:
                continue
            files.extend(find_files(f'{full_path}/'))

        elif _path.endswith('.py'):
            files.append(f'{path}{_path}')
    return files


def read_or_create_mkdocs(base_directory: str) -> str:
    mkdocs_path = f'{base_directory}mkdocs.yml'

    # Create If Not Exists
    if not os.path.exists(mkdocs_path):
        with open(mkdocs_path, 'w') as file:
            txt = f"""site_name: Documentations
        docs_dir: "{base_directory}docs{base_directory}"
        repo_url: "https://github.com/DigifyShop/django-doc/blog/master/"
        
        theme:
          name: material
        """
            file.write(txt)

    # Read MkDocs
    with open(mkdocs_path, 'r') as f:
        data = yaml.safe_load(f)
        repo_url = data.get('repo_url')
    print('ok:', repo_url)
    return repo_url


def run(base_directory: str):
    if base_directory[-1] != '/':
        base_directory += '/'
    python_files = find_files(base_directory)

    if repo_url := read_or_create_mkdocs(base_directory) is None:
        return 'Replace the sample "repo_url" in mkdocs.yml and try again.'
    for file in python_files:
        MakeDocstring(file, base_directory=base_directory, repo_url=repo_url)

