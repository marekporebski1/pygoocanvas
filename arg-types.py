from argtypes import ArgType, matcher
import reversewrapper

class CairoMatrixArg(ArgType):

    before = ('    %(name)s = &((PycairoMatrix*)(py_%(name)s))->matrix;\n')

    def write_param(self, ptype, pname, pdflt, pnull, info):
        info.varlist.add('PyObject', '*py_' + pname)
        info.varlist.add('cairo_matrix_t', '*'+pname)
        info.add_parselist('O', ['&py_'+pname], [pname])
        info.arglist.append(pname)
        info.codebefore.append (self.before % { 'name' : pname, 'namecopy' : 'NULL' })


    def write_return(self, ptype, ownsreturn, info):
        info.varlist.add('cairo_matrix_t', '*ret')
        info.codeafter.append('   return PycairoMatrix_FromMatrix(ret);\n');

matcher.register('cairo_matrix_t*', CairoMatrixArg())


class CairoParam(reversewrapper.Parameter):
    def get_c_type(self):
        return self.props.get('c_type').replace('const-', 'const ')
    def convert_c2py(self):
        self.wrapper.add_declaration("PyObject *py_%s;" % self.name)
        self.wrapper.write_code(
            code=('py_%s = PycairoContext_FromContext(cairo_reference(%s), NULL, NULL);' %
                  (self.name, self.name)),
            cleanup=("Py_DECREF(py_%s);" % self.name))
        self.wrapper.add_pyargv_item("py_%s" % self.name)

matcher.register_reverse("cairo_t*", CairoParam)

class BoundsPtrArg(ArgType):

    def write_param(self, ptype, pname, pdflt, pnull, info):
        info.varlist.add('PyObject', '*py_' + pname)
        info.add_parselist('O!', ['&PyGooCanvasBounds_Type', '&py_'+pname], [pname])
        info.arglist.append("&((PyGooCanvasBounds *) py_%s)->bounds" % (pname,))

    def write_return(self, ptype, ownsreturn, info):
        info.varlist.add('GooCanvasBounds', '*ret')
        info.codeafter.append('   return pygoo_canvas_bounds_new(ret);\n');

matcher.register('GooCanvasBounds*', BoundsPtrArg())

class GooCanvasBoundPtrReturn(reversewrapper.ReturnType):
    def get_c_type(self):
        return self.props.get('c_type')
    def write_decl(self):
        self.wrapper.add_declaration("%s retval;" % self.get_c_type())
        self.wrapper.add_declaration("PyObject *py_bounds;")
    def write_error_return(self):
        self.wrapper.write_code("return NULL;")
    def write_conversion(self):
        self.wrapper.add_pyret_parse_item("O!", "&PyGooCanvasBounds_Type, &py_bounds", prepend=True)
        self.wrapper.write_code((
            " /* FIXME: this leaks memory */\n"
            "retval = g_new(GooCanvasBounds, 1);\n"
            "*retval = ((PyGooCanvasBounds*) py_bounds)->bounds;"),
                                code_sink=self.wrapper.post_return_code)

matcher.register_reverse_ret("GooCanvasBounds*", GooCanvasBoundPtrReturn)

class GObjectReturn(reversewrapper.ReturnType):

    def get_c_type(self):
        return self.props.get('c_type', 'GObject *')

    def write_decl(self):
        self.wrapper.add_declaration("%s retval;" % self.get_c_type())

    def write_error_return(self):
        self.wrapper.write_code("return NULL;")

    def write_conversion(self):
        self.wrapper.write_code(
            code=None,
            failure_expression="py_retval == Py_None")
        self.wrapper.write_code(
            code=None,
            failure_expression="!PyObject_TypeCheck(py_retval, &PyGObject_Type)",
            failure_exception='PyErr_SetString(PyExc_TypeError, "retval should be a GObject");')
        self.wrapper.write_code("retval = (%s) pygobject_get(py_retval);"
                                % self.get_c_type())
        self.wrapper.write_code("g_object_ref((GObject *) retval);")

matcher.register_reverse_ret('GObject*', GObjectReturn)
