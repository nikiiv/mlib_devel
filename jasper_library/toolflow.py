"""
A python-based toolflow to build a vivado
project from a simulink design, using the
CASPER xps library.

A work in progress.
"""
import logging
import os
import casper_platform as platform
import yellow_blocks.yellow_block as yellow_block
import verilog
from constraints import PortConstraint, ClockConstraint, GenClockConstraint, \
    ClockGroupConstraint, InputDelayConstraint, OutputDelayConstraint, MaxDelayConstraint, \
    MinDelayConstraint, FalsePathConstraint, MultiCycleConstraint, RawConstraint
import castro
import helpers
import yaml
import glob
import time
import hashlib  # Added to calculate md5hash of .bin bitstream and add it to the .fpg header
import pickle   # Used to dump the pickle of the generated VerilogModule to the build directory for debugging
import struct   # Used to append a binary checksum to a bitstream
# For xml2vhdl generation from Oxford
import xml.dom.minidom
import xml.etree.ElementTree as ET

#JH: I don't know what this is, but I suspect here is a better place for it than constraints.py
MAX_IMAGE_CHUNK_SIZE = 1988

try:
    from katversion import get_version as kat_get_version
except ImportError:
    kat_get_version = None


class Toolflow(object):
    """
    A class embodying the main functionality of the toolflow.
    This class is responsible for generating a complete
    top-level verilog description of a project from a 'peripherals file'
    which encodes information about which IP a user wants instantiated.

    The toolflow class can parse such a file, and use it to generate verilog,
    a list of source files, and a list of constraints.
    These can be passed off to a toolflow backend to be turned into some
    vendor-specific platform and compiled. At least, that's the plan...
    """

    def __init__(self, frontend='simulink', compile_dir='/tmp',
                 frontend_target='/tmp/test.slx', jobs=8):
        """
        Initialize the toolflow.

        :param frontend: Name of the toolflow frontend to use.
            Currently only ``simulink`` is supported
        :type frontend: str
        :param compile_dir: Compile directory where build files and logs
            should go.
        """
        # Set up a logger (the logger named 'jasper' should already
        # have been configured beforehand
        self.logger = logging.getLogger('jasper.toolflow')
        self.jobs = jobs

        self.logger.info('Starting Toolflow!')
        self.logger.info('Frontend is %s' % frontend)

        self.compile_dir = compile_dir.rstrip('/')
        self.output_dir = self.compile_dir + '/outputs'

        self.logger.info('Setting compile directory: %s' % self.compile_dir)
        os.system('mkdir -p %s' % self.compile_dir)
        os.system('mkdir -p %s' % self.output_dir)

        # compile parameters which can be set straight away
        self.start_time = time.localtime()
        self.periph_file = self.compile_dir + '/jasper.per'
        self.git_info_file = self.compile_dir + '/git_info.tab'
        self.frontend_target = frontend_target
        self.modelname = frontend_target.split('/')[-1][:-4]  # strip off extension
        self.frontend_target_base = os.path.basename(frontend_target)

        self.cores = None
        self.topfile = None
        self.top = None
        self.periph_objs = None
        self.constraints = None

        if frontend == 'simulink':
            self.frontend = SimulinkFrontend(compile_dir=self.compile_dir,
                                             target=frontend_target)
        else:
            self.logger.error('Unsupported toolflow frontent: %s' % frontend)
            raise Exception('Unsupported toolflow frontend: %s' % frontend)

        self.backend = None
        # if backend == 'vivado':
        #    self.backend = VivadoBackend(compile_dir=self.compile_dir)
        # elif backend == 'ise':
        #    self.backend = ISEBackend(compile_dir=self.compile_dir)
        # else:
        #    self.logger.error('Unsupported toolflow backend: %s'%backend)
        #    raise Exception('Unsupported toolflow backend: %s'%backend)

        self.sources = []
        self.ips = []
        self.tcl_sources = []
        self.const_files = []

        # compile directories for xml2vhdl
        self.xml_source_dir = self.compile_dir + '/xml2vhdl_source'
        self.xml_output_dir = self.compile_dir + '/xml2vhdl_xml_output'
        self.hdl_output_dir = self.compile_dir + '/xml2vhdl_hdl_output'

    def exec_flow(self, gen_per=True, frontend_compile=True):
        """
        Execute a compile.

        :param gen_per: Have the toolflow frontend generate a fresh
            peripherals file
        :type gen_per: bool
        :param frontend_compile: Run the frontend compiler (eg. System
            Generator)
        :type frontend_compile: bool
        """

        if gen_per:
            self.frontend.gen_periph_file(fname=self.periph_file)
            self.frontend.write_git_info_file(fname=self.git_info_file)

        # Have the toolflow parse the information from the
        # frontend and generate the YellowBlock objects
        self.logger.info('Generating peripheral objects')
        self.gen_periph_objs()

        # Copy the platforms top-level hdl file
        # and begin modifying it based on the yellow
        # block objects.
        self.logger.info('Generating HDL')
        self.build_top()
        self.generate_hdl()
        # Generate constraints (not yet xilinx standard)
        self.generate_consts()
        # Generate software cores file
        self.write_core_info()
        self.write_core_jam_info()
        # print 'Initializing backend project'
        # self.backend.initialize(self.plat)

        self.constraints_rule_check()

        if frontend_compile:
            # Run system generator (maybe flow-wise
            # it would make sense to run this sooner,
            # but since it's the longest single step
            # it's nice to run it at the end, so there's
            # an opportunity to catch toolflow errors
            # before waiting for it
            self.logger.info('Running frontend compile')
            # skip this step if you don't want to wait for sysgen in testing
            self.frontend.compile_user_ip(update=True)
            self.logger.info('frontend complete')

        self.dump_castro(self.compile_dir+'/castro.yml')

        # binary = self.backend.binary_loc
        # os.system('cp %s %s/top.bin'%(binary, self.compile_dir))
        # mkbof_cmd = '%s/jasper_library/mkbof_64 -o %s/%s -s %s/core_info.ta' \
        #             'b -t 3 %s/top.bin' % (os.getenv('MLIB_DEVEL_PATH'),
        #                                    self.output_dir, self.output,
        #                                    self.compile_dir, self.compile_dir)
        # os.system(mkbof_cmd)
        # self.logger.info(mkbof_cmd)

    def check_attr_exists(self, thing, generator):
        """
        Lots of methods in this class require that certain attributes
        have been set by other methods before proceeding. This is probably
        a symptom of the code being terribly structured. This method
        checks if an attribute exists and throws an error message if not.
        In principle it could automatically run the necessary missing steps,
        but that seems pretty suspect.

        :param thing: Attribute to check.
        :type thing: str
        :param generator: Method which can be used to set thing (used for
            error message only)
        :type generator: str
        """
        if self.__getattribute__(thing) is None:
            errmsg = '%s is not defined. Have you run %s yet?' % (
                thing, generator)
            self.logger.error(errmsg)
            raise AttributeError(errmsg)

    def _add_external_tcl(self):
        """
        Add tcl commands from the frontend
        """
        raise DeprecationWarning
        for fname in self.tcl_sources:
            with open(fname, 'r') as fh:
                self.backend.add_tcl_cmd(fh.read())

    def generate_hdl(self):
        """
        Generates a top file for the target platform
        based on the peripherals file.

        Internally, calls:

        * ``instantiate_periphs``: call each yellow block's mod_top method
        * ``instantiate_user_ip``: add ports to top module based on port entries in peripheral file
        * ``regenerate_top``: rewrite top.v
        """
        self.logger.info('instantiating user peripherals')
        self._instantiate_periphs()
        self.logger.info('instantiating user_ip')
        self._instantiate_user_ip()
        self.logger.info('regenerating top')
        self.regenerate_top()

    def _parse_periph_file(self):
        """
        Open the peripherals file and parse it's
        contents using the pyaml package.
        Write the resulting yellow_blocks
        and user_modules dictionaries to
        attributes
        """
        if not os.path.exists(self.periph_file):
            self.logger.error('Peripherals file doesn\'t exist!')
            raise Exception('Peripherals file doesn\'t exist!')
        with open(self.periph_file, 'r') as fh:
            yaml_dict = yaml.load(fh, Loader=yaml.Loader)
        self.peripherals = yaml_dict['yellow_blocks']
        self.user_modules = yaml_dict['user_modules']

    def _extract_plat_info(self):
        """
        Extract platform information from the
        yellow_block attributes.
        Use this to instantiate the appropriate
        device from the Platform class.
        """
        for key in list(self.peripherals.keys()):
            if self.peripherals[key]['tag'] == 'xps:xsg':
                # self.plat = platform.Platform.get_loader(
                #     self.peripherals[key]['hw_sys'])
                self.plat = platform.Platform(
                    self.peripherals[key]['hw_sys'].split(':')[0])
                # self.backend.plat = self.plat
                self.clk_src = self.peripherals[key]['clk_src']
                # in MHz
                self.clk_rate = float(self.peripherals[key]['clk_rate'])
                return
        raise Exception('self.peripherals does not contain anything '
                        'tagged xps:xsg')

    def _drc(self):
        """
        Get the provisions of the active platform and yellow blocks
        and compare with the current requirements of blocks in the design.
        """
        provisions = self._get_provisions()
        # check all requirements and exclusive reqs are provided
        for obj in self.periph_objs:
            for req_list in [obj.requires, obj.exc_requires]:
                for req in req_list:
                    self.logger.debug('%s requires %s' % (obj.name, req))
                    if req not in provisions:
                        self.logger.error('NOT SATISFIED: %s requires %s' % (
                            obj.name, req))
                        raise Exception('DRC FAIL! %s (required by %s) not '
                                        'provided by platform or any '
                                        'peripheral' % (req, obj.name))
        # check for overallocation of resources
        used = []
        for obj in self.periph_objs:
            for req in obj.exc_requires:
                self.logger.debug('%s requires %s exclusively' % (
                    obj.name, req))
                if req in used:
                    raise Exception('DRC FAIL! %s requires %s, but it has '
                                    'already been used by another block.'
                                    '' % (obj.name, req))
                else:
                    used.append(req)

    def _get_provisions(self):
        """
        Get and return all the provisions of the active platform and
        yellow blocks.
        """
        provisions = []
        for obj in self.periph_objs:
            provisions += obj.provides
        provisions += self.plat.provides
        return provisions

    def build_top(self):
        """
        Copies the base top-level verilog file (which is platform
        dependent) to the compile directory.
        Constructs an associated VerilogModule instance ready to be
        modified.
        """
        try:
            # generate multiboot, golden or tooflow image based on yaml file
            self.hdl_filename = '%s/skarab_infr/%s_parameters.vhd' % (os.getenv('HDL_ROOT'), self.plat.name)
            # check to see if parameter file exists. Some platforms may not use this.
            if os.path.isfile(self.hdl_filename):
                self._gen_hdl_version(filename_hdl=self.hdl_filename)
        except KeyError:
            s = ""
        # check to see if entity file exists. Some platforms may not use this. This function overwrites incorrectly
        # generated sysgen hdl files
        #if self.platform.conf['bit_reversal']==True:
        try:
            # return the sysgen entity declarations file
            self.hdl_sysgen_filename = '%s/sysgen/hdl_netlist/%s.srcs/sources_1/imports/sysgen/%s_entity_declarations.vhd' \
                                       % (self.compile_dir, self.modelname, self.modelname)
            if os.path.isfile(self.hdl_sysgen_filename):
                self._gen_hdl_simulink(hdl_sysgen_filename=self.hdl_sysgen_filename)
        # just ignore if key is not present as only some platforms will have the key.
        except KeyError:
            s = ""
        self.topfile = self.compile_dir+'/top.v'
        # delete top.v file if it exists, otherwise synthesis will fail
        if os.path.exists(self.topfile):
            os.remove(self.topfile)
        # os.system('cp %s %s'%(basetopfile, self.topfile))
        self.sources.append(self.topfile)
        for source in self.plat.sources:
            self.sources.append(os.getenv('HDL_ROOT')+'/'+source)
        for source in self.plat.consts:
            self.const_files.append(os.getenv('HDL_ROOT') + '/%s/%s' % (
                self.plat.name, source))
        if os.path.exists(self.topfile):
            self.top = verilog.VerilogModule(name='top', topfile=self.topfile)
        else:
            self.top = verilog.VerilogModule(name='top')

    def gen_periph_objs(self):
        """
        Generate a list of yellow blocks from the current peripheral file.

        Internally, calls:

        * ``_parse_periph_file``: parses .per file
        * ``_extract_plat_info``: instantiates platform instance

        Then calls each yellow block's constructor.
        Runs a system-wide drc before returning.
        """
        
        
        self._parse_periph_file()
        self._extract_plat_info()
        self.periph_objs = []
        
        for pk in list(sorted(self.peripherals.keys())):
            self.logger.debug('Generating Yellow Block: %s' % pk)
            self.periph_objs.append(yellow_block.YellowBlock.make_block(
                self.peripherals[pk], self.plat))
        self._expand_children(self.periph_objs)
        
        self._drc()
        
    def _expand_children(self, population, parents=None, recursive=True):
        """
        :param population: yellow blocks to which children will be added
        :type population: list
        :param parents: yellow blocks which will be invited to procreate.
            If parents = None, the population will be used as the initial
            parents argument
        :type parents: list
        :param recursive: if True, this method is called recursively, with children
            passed as the new parents argument. The population list
            will continue to grow until no child yellow blocks wish
            to procreate any further.
        :type recursive: bool
        """
        parents = parents or population
        children = []
        for parent in parents:
            self.logger.debug('Inviting block %r to procreate' % parent)
            children += parent.gen_children()
        if not children:
            return
        else:
            population += children
            if not recursive:
                return
            else:
                self._expand_children(population, children)
                return

    def _instantiate_periphs(self):
        """
        Calls each yellow block's modify_top method against the class'
        top VerilogModule instance
        """
        self.logger.info('top: %s' % self.topfile)
        for obj in self.periph_objs:
            self.logger.debug('modifying top for obj %s' % obj.name)
            # self.top.set_cur_blk(obj.fullname)
            if '/' in obj.fullpath:
                obj.fullpath = obj.fullpath.partition('/')[2]
            self.top.set_cur_blk('%s: %s'%(obj.tag.split(':')[1], obj.fullpath))
            obj.modify_top(self.top)
            self.sources += obj.sources
            self.ips += obj.ips
        # add AXI4-Lite architecture specfic stuff, which must be called after all yellow blocks have modified top.
        if self.plat.mmbus_architecture == 'AXI4-Lite':
            # Make an AXI4-Lite interconnect yellow block and let it modify top
            axi4lite_interconnect = yellow_block.YellowBlock.make_block(
                {'tag': 'xps:axi4lite_interconnect', 'name': 'axi4lite_interconnect', 
                'fullpath': list(sorted(self.user_modules.keys()))[0] +'/axi4lite_interconnect'}, self.plat)
            axi4lite_interconnect.modify_top(self.top)
            # Generate xml2vhdl
            self.xml2vhdl()
            # add the AXI4lite yellowblock to the peripherals manually
            self.periph_objs.append(axi4lite_interconnect)

    def _instantiate_user_ip(self):
        """
        Adds VerilogInstance and ports associated with user-ip to the class' top
        VerilogModule instance.
        """
        for name, usermodule in list(self.user_modules.items()):
            inst = self.top.get_instance(entity=name, name='%s_inst' % name)
            self.top.set_cur_blk('usermodule: %s'%name)
            # internal = False --> we assume that other yellow
            # blocks have set up appropriate signals in top.v
            # (we can't add them here anyway, because we don't
            # know the port widths)
            if 'clock' in list(sorted(usermodule.keys())):
                inst.add_port(name=usermodule['clock'], signal='user_clk',
                              parent_sig=False)
            if 'clock_enable' in list(sorted(usermodule.keys())):
                inst.add_port(name=usermodule['clock_enable'], signal='1\'b1',
                              parent_sig=False)
            for port in usermodule['ports']:
                inst.add_port(name=port, signal=port, parent_sig=False)

            if usermodule['sources'] is not None:
                for source in usermodule['sources']:
                    self.sources += glob.glob(source)
            # if usermodule['tcl_sources'] is not None:
            #    for source in usermodule['tcl_sources']:
            #        self.tcl_sources += glob.glob(source)

    def write_core_info(self):
        if self.plat.mmbus_architecture == 'AXI4-Lite':
            # get list of all axi4lite_devices in self.top.memory_map dict
            self.cores = []
            for val in list(self.top.memory_map.values()):
                self.cores += val['axi4lite_devices']
        else:
            self.cores = self.top.wb_devices
        basefile = '%s/%s/core_info.tab' % (os.getenv('HDL_ROOT'),
                                            self.plat.name)
        newfile = '%s/core_info.tab' % self.compile_dir
        self.logger.debug('Opening %s' % basefile)
        modemap = {'rw': 3, 'r': 1, 'w': 2}
        try:
            with open(basefile, 'r') as fh:
                s = fh.read()
        # If there isn't a basefile, just plow on
        except IOError:
            s = ''
        if len(self.cores) != 0:
            longest_name = max([len(core.regname) for core in self.cores])
            format_str = '{0:%d} {1:1} {2:<16x} {3:<16x}\n' % longest_name
        for core in self.cores:
            self.logger.debug('Adding core_info.tab entry for '
                              '%s' % core.regname)
            s += format_str.format(core.regname, modemap[core.mode],
                                   core.base_addr, core.nbytes)
            # add aliases if the WB Devices have them
            for reg in core.memory_map:
                s += format_str.format(reg.name, modemap[reg.mode],
                                       core.base_addr + reg.offset, reg.nbytes)
            # s += '%s\t%d\t%x\t%x\n'%(core.regname, modemap[core.mode],
            #                          core.base_addr, core.nbytes)
        self.logger.debug('Opening %s' % basefile)
        with open(newfile, 'w') as fh:
            fh.write(s)

    def write_core_jam_info(self):
        if self.plat.mmbus_architecture == 'AXI4-Lite':
            # get list of all axi4lite_devices in self.top.memory_map dict
            self.cores = []
            for val in list(self.top.memory_map.values()):
                self.cores += val['axi4lite_devices']
        else:
            self.cores = self.top.wb_devices
        basefile = '%s/%s/core_info.jam.tab' % (os.getenv('HDL_ROOT'), self.plat.name)
        newfile = '%s/core_info.jam.tab' % self.compile_dir
        self.logger.debug('Opening %s' % basefile)
        modemap = {'rw': 3, 'r': 1, 'w': 2}
        try:
            with open(basefile, 'r') as fh:
               s = fh.read()
        # If there isn't a basefile, just plow on
        except IOError:
            s = ''
        if len(self.cores) != 0:
            longest_name = max([len(core.regname) for core in self.cores])
            format_str = '{0:%d} {1:1} {2:<16x} {3:<16x} {4:<2x}\n' % longest_name
        for core in self.cores:
            self.logger.debug('Adding core_info.jam.tab entry for %s' % core.regname)
            s += format_str.format(core.regname, modemap[core.mode], core.base_addr, core.nbytes, core.typecode)
            # add aliases if the WB Devices have them
            for reg in core.memory_map:
                s += format_str.format(reg.name, modemap[reg.mode], core.base_addr + reg.offset, reg.nbytes, core.typecode)
            # s += '%s\t%d\t%x\t%x\n'%(core.regname, modemap[core.mode], core.base_addr, core.nbytes)
        self.logger.debug('Opening %s' % basefile)
        with open(newfile, 'w') as fh:
            fh.write(s)
        # generate the binary and xilinx-style .mem versions of this table,
        # using Python script [TODO convert to a callable function?].
        ret = os.system('python %s/jasper_library/cit2csl.py -b %s > %s.bin' % (os.getenv('MLIB_DEVEL_PATH'), newfile, newfile))
        if ret != 0:
            errmsg = 'Failed to generate binary file {}.bin, error code {}.'.format(newfile,ret)
            self.logger.error(errmsg)
            raise Exception(errmsg)
        ret = os.system('python %s/jasper_library/cit2csl.py %s > %s.mem' % (os.getenv('MLIB_DEVEL_PATH'), newfile, newfile))
        if ret != 0:
            errmsg = 'Failed to generate xilinx-style file {}.mem, error code {}.'.format(newfile,ret)
            self.logger.error(msg)
            raise Exception(errmsg)

    def regenerate_top(self):
        """
        Generate the verilog for the modified top
        module. This involves computing the wishbone
        interconnect / addressing and generating new
        code for yellow block instances.
        """
        # Decide if we're going to use a hierarchical arbiter.
        self.logger.debug("Looking for a max_devices_per_arbiter spec")
        if 'max_devices_per_arbiter' in self.plat.conf:
            self.top.max_devices_per_arb = self.plat.conf['max_devices_per_arbiter']
            self.logger.debug("Found max_devices_per_arbiter: %s" % self.top.max_devices_per_arb)
        # Check for memory map bus architecture, added to support AXI4-Lite
        if self.plat.mmbus_architecture == 'AXI4-Lite':
            pass
        else:
            self.top.wb_compute(self.plat.dsp_wb_base_address,
                            self.plat.dsp_wb_base_address_alignment)
        # Write top module file
        self.top.gen_module_file(filename=self.compile_dir+'/top.v')
        # Write any submodule files required for the compile. This is probably
        # only the hierarchical WB arbiter, or nothing at all
        for key, val in self.top.generated_sub_modules.items():
            self.logger.info("Writing sub module file %s.v" % key)
            with open(self.compile_dir+'/%s.v'%key, 'w') as fh:
                fh.write(val)
                self.sources.append(fh.name)
        self.logger.info("Dumping pickle of top-level Verilog module")
        pickle.dump(self.top, open('%s/top.pickle' % self.compile_dir,'wb'))

    def generate_consts(self):
        """
        Compose a list of constraints from each yellow block.
        Use platform information to generate the appropriate
        physical realisation of each constraint.
        """
        self.logger.info('Extracting constraints from peripherals')
        self.check_attr_exists('periph_objs', 'gen_periph_objs()')
        self.constraints = []
        for obj in self.periph_objs:
            c = obj.gen_constraints()
            if c is not None:
                self.constraints += c
        self.logger.info('Generating physical constraints')
        for constraint in self.constraints:
            try:
                constraint.gen_physical_const(self.plat)
            except AttributeError:
                pass  # some constraints don't have this method
        # check for any funny business
        # used_pins = []
        # for constraint in self.constraints:

    def constraints_rule_check(self):
        """
        Check pin constraints against top level signals.
        Warn about missing constraints.
        """
        self.logger.info('Carrying out constraints rule check')
        port_constraints = []
        for const in self.constraints:
            if isinstance(const, PortConstraint):
                port_constraints += [const.portname]
        for key in list(sorted(self.top.ports.keys())):
            for port in self.top.ports[key]:
                if port not in port_constraints:
                    self.logger.warning('Port %s (instantiated by %s) has no constraints!' % (port, key))
        self.logger.info('Constraint rule check complete')

    def dump_castro(self, filename):
        """
        Build a 'standard' Castro object, which is the
        interface between the toolflow and the backends.
        """
        import castro

        c = castro.Castro('top', self.sources, self.ips)

        # build castro standard pin constraints
        pin_constraints = []
        clk_constraints = []
        gen_clk_constraints = []
        clk_grp_constraints = []
        input_delay_constraints = []
        output_delay_constraints = []
        max_delay_constraints = []
        min_delay_constraints = []
        false_path_constraints = []
        multi_cycle_constraints = []
        raw_constraints = []

        for const in self.constraints:
            if isinstance(const, PortConstraint):
                pin_constraints += [castro.PinConstraint(
                    portname=const.portname,
                    symbolic_name=const.iogroup,
                    portname_indices=const.port_index,
                    symbolic_indices=const.iogroup_index,
                    io_standard=const.iostd,
                    location=const.loc
                    )]
            elif isinstance(const, ClockConstraint):
                clk_constraints += [castro.ClkConstraint(
                    portname=const.signal,
                    freq_mhz=const.freq,
                    period_ns=const.period,
                    clkname=const.name,
                    waveform_min_ns=const.waveform_min,
                    waveform_max_ns=const.waveform_max,
                    port_en=const.port_en,
                    virtual_en=const.virtual_en
                    )]
            elif isinstance(const, GenClockConstraint):
                gen_clk_constraints += [castro.GenClkConstraint(
                    pinname=const.signal,
                    clkname=const.name,
                    divide_by=const.divide_by,
                    clksource=const.clock_source
                    )]
            elif isinstance(const, ClockGroupConstraint):
                clk_grp_constraints += [castro.ClkGrpConstraint(
                    clknamegrp1=const.clock_name_group_1,
                    clknamegrp2=const.clock_name_group_2,
                    clkdomaintype=const.clock_domain_relationship
                    )]
            elif isinstance(const, InputDelayConstraint):
                input_delay_constraints += [castro.InDelayConstraint(
                    clkname=const.clkname,
                    consttype=const.consttype,
                    constdelay_ns=const.constdelay_ns,
                    add_delay_en=const.add_delay_en,
                    portname=const.portname
                )]
            elif isinstance(const, OutputDelayConstraint):
                output_delay_constraints += [castro.OutDelayConstraint(
                    clkname=const.clkname,
                    consttype=const.consttype,
                    constdelay_ns=const.constdelay_ns,
                    add_delay_en=const.add_delay_en,
                    portname=const.portname
                )]
            elif isinstance(const, MaxDelayConstraint):
                max_delay_constraints += [castro.MaxDelayConstraint(
                    sourcepath=const.sourcepath,
                    destpath=const.destpath,
                    constdelay_ns=const.constdelay_ns
                )]
            elif isinstance(const, MinDelayConstraint):
                min_delay_constraints += [castro.MinDelayConstraint(
                    sourcepath=const.sourcepath,
                    destpath=const.destpath,
                    constdelay_ns=const.constdelay_ns
                )]
            elif isinstance(const, FalsePathConstraint):
                false_path_constraints += [castro.FalsePthConstraint(
                    sourcepath=const.sourcepath,
                    destpath=const.destpath
                )]
            elif isinstance(const, MultiCycleConstraint):
                multi_cycle_constraints += [castro.MultiCycConstraint(
                    multicycletype=const.multicycletype,
                    sourcepath=const.sourcepath,
                    destpath=const.destpath,
                    multicycledelay=const.multicycledelay
                )]
            elif isinstance(const, RawConstraint):
                raw_constraints += [castro.RawConstraint(
                    const.raw)]

        c.synthesis = castro.Synthesis()
        c.synthesis.pin_constraints = pin_constraints
        c.synthesis.clk_constraints = clk_constraints
        c.synthesis.gen_clk_constraints = gen_clk_constraints
        c.synthesis.clk_grp_constraints = clk_grp_constraints
        c.synthesis.input_delay_constraints = input_delay_constraints
        c.synthesis.output_delay_constraints = output_delay_constraints
        c.synthesis.max_delay_constraints = max_delay_constraints
        c.synthesis.min_delay_constraints = min_delay_constraints
        c.synthesis.false_path_constraints = false_path_constraints
        c.synthesis.multi_cycle_constraints = multi_cycle_constraints
        c.synthesis.raw_constraints = raw_constraints
        c.synthesis.platform_name = self.plat.name
        c.synthesis.fpga_manufacturer = self.plat.manufacturer
        c.synthesis.fpga_model = self.plat.fpga
        c.synthesis.pin_map = self.plat._pins

        mm_slaves = []
        if self.plat.mmbus_architecture == 'AXI4-Lite':
            for dev in self.top.axi4lite_devices:
                if dev.mode == 'rw':
                    mode = 3
                elif dev.mode == 'r':
                    mode = 1
                elif dev.mode == 'w':
                    mode = 2
                else:
                    mode = 1
                mm_slaves += [castro.mm_slave(dev.regname, mode, dev.base_addr,
                                            dev.nbytes)]
        else:
            for dev in self.top.wb_devices:
                if dev.mode == 'rw':
                    mode = 3
                elif dev.mode == 'r':
                    mode = 1
                elif dev.mode == 'w':
                    mode = 2
                else:
                    mode = 1
                mm_slaves += [castro.mm_slave(dev.regname, mode, dev.base_addr,
                                            dev.nbytes)]

        c.mm_slaves = mm_slaves

        with open(filename, 'w') as fh:
            fh.write(yaml.dump(c))

    def _gen_hdl_version(self, filename_hdl):
        """
        This function reads the existing version information from the HDL file and rewrites the version information and
        appends it with an "8" (golden), "4" (multiboot) or "0" (toolflow)

        :param filename_hdl: This is the path and hdl file that
            contains the original FPGA version information. This file is overwritten with new multiboot, toolflow or
             golden image info before being imported to the compile directory
            directory
        :type filename_bin: str
        """

        stringToMatch = 'constant C_VERSION'
        lines = []
        self.logger.debug('Opening Original hdl file %s' % filename_hdl)
        # read version info from original file and write appended version info to a new list that will be
        # written into a new file
        with open(filename_hdl, 'r') as fh1:
            for line in fh1:
                if stringToMatch in line:
                    if self.plat.boot_image == 'golden':
                        linesub = line[:line.find('X')+2] +'8'+ line[line.find('X')+3:]
                        lines.append(linesub)
                    elif self.plat.boot_image == 'multiboot':
                        linesub = line[:line.find('X')+2] +'4'+ line[line.find('X')+3:]
                        lines.append(linesub)
                    else:
                        linesub = line[:line.find('X')+2] +'0'+ line[line.find('X')+3:]
                        lines.append(linesub)
                else:
                    lines.append(line)
            #print (lines)
        fh1.close()

        # write new version info to the same file that will be imported to the correct folder
        with open(filename_hdl, 'w') as fh2:
                fh2.writelines(lines)
        fh2.close()

    
    def generate_xml_memory_map(self, memory_map):
        """
        Generate xml memory map files that represent each AXI4-Lite interface for Oxford's xml2vhdl.
        """
        # Generate memory map xml file for each interface in memory_map

        for interface in list(sorted(memory_map.keys())):
            xml_root = ET.Element('node')
            xml_root.set('id', interface)
            # fill xml node with slave info from memory map
            for reg in memory_map[interface]['memory_map']:
                # add a child to parent node
                node = ET.SubElement(xml_root, 'node')
                node.set('id', reg.name)
                node.set('address', "%s" % hex(reg.offset))
                # toolflow only currently supports 32-bit registers
                node.set('mask', hex(0xFFFFFFFF))
                # node.set('size', str(reg.nbytes))
                node.set('permission', reg.mode)               
                node.set('axi4lite_mode', reg.axi4lite_mode)
                if reg.mode == 'r':
                    if reg.default_val != 0:
                       # Populate defaults of sys_block version registers
                       node.set('hw_rst', str(reg.default_val))
                    else:
                       # Basically a To Processor register (status)
                       node.set('hw_permission', 'w')
                else:
                    # Only for a From Processor register (control)
                    node.set('hw_rst', str(reg.default_val))
                # Best we can currently do for a description...? haha
                node.set('description', str(interface + "_" + reg.name))
                # set bram size and 
                if hasattr(reg, 'ram') and reg.ram==True:
                    node.set('hw_dp_ram', 'yes')
                    node.set('size', str(reg.nbytes//4)) # this needs to be in words not bytes!!! Dammit Janet

                    # Need to make special mention of the bitwidth (data width) here
                    # - Reading from xml2slave.py - need the key 'hw_dp_ram_width'
                    node.set('hw_dp_ram_width', str(reg.data_width))

            # output xml file describing memory map as input for xml2vhdl
            myxml = xml.dom.minidom.parseString(ET.tostring(xml_root))
            xml_base_name = interface + "_memory_map.xml"
            xml_file_name = os.path.join(self.xml_source_dir, xml_base_name)
            xml_file = open(xml_file_name, "w")
            xml_text = myxml.toprettyxml()
            xml_text += "<!-- This file has been automatically generated by generate_xml_memory_map function." + " /!-->\n"
            xml_file.write(xml_text)
            xml_file.close()

    def generate_xml_ic(self, memory_map):
        """
        Generate xml interconnect file that represent top-level AXI4-Lite interconnect for Oxford's xml2vhdl.
        """
        # loop over interfaces, sort by address, make interconnect
        xml_root = ET.Element('node')
        xml_root.set('id', 'axi4lite_top')
        xml_root.set('address', hex(self.plat.mmbus_base_address))
        xml_root.set('hw_type', 'ic')
        for interface in list(sorted(memory_map.keys())):
            # add a child to parent node
            node = ET.SubElement(xml_root, 'node')
            node.set('id', interface)
            node.set('address', "%s" % memory_map[interface]['relative_address'])
            node.set('link', "%s" % interface + "_memory_map_output.xml")

        # output xml file describing interconnect as input for xml2vhdl
        myxml = xml.dom.minidom.parseString(ET.tostring(xml_root))
        xml_base_name = "axi4lite_top_ic_memory_map.xml"
        xml_file_name = os.path.join(self.xml_source_dir, xml_base_name)
        xml_file = open(xml_file_name, "w")
        xml_text = myxml.toprettyxml()
        xml_text += "<!-- This file has been automatically generated by generate_xml_memory_map function." + " /!-->\n"
        xml_file.write(xml_text)
        xml_file.close()

    def xml2vhdl(self):
        """
        Function to call Oxford's python code to generate AXI4-Lite VHDL register 
        interfaces from an XML memory map specification.

        Obtained from: https://bitbucket.org/ricch/xml2vhdl/src/master/
        """
        from xml2vhdl.xml2vhdl import Xml2VhdlGenerate, helper
        # make input and output directories
        if not os.path.exists(self.xml_source_dir):
            os.makedirs(self.xml_source_dir)
        if not os.path.exists(self.xml_output_dir):
            os.makedirs(self.xml_output_dir)
        if not os.path.exists(self.hdl_output_dir):
            os.makedirs(self.hdl_output_dir)
        # generate xml memory maps for input
        self.generate_xml_memory_map(self.top.memory_map)
        # generate xml interconnect for input
        self.generate_xml_ic(self.top.memory_map)
        # execute xml2vhdl generation

        try:
            # Xml2VhdlGenerate takes arguments as attributes of an args class
            args = helper.arguments.Arguments()
            # see the help of the xml2vhdl.py script
            args.input_folder  = [self.xml_source_dir] # Needs to be a list (can be multiple directories)
            args.vhdl_output   = self.hdl_output_dir
            args.xml_output    = self.xml_output_dir
            args.bus_library   = "xil_defaultlib"
            args.slave_library = "xil_defaultlib"
            self.logger.info("Trying to generate AXI HDL from XML")
            self.logger.info("  Input directory: %s" % args.input_folder)
            self.logger.info("  Output XML directory: %s" % args.xml_output)
            self.logger.info("  Output directory: %s" % args.vhdl_output)
            self.logger.info("  Slave library: %s" % args.slave_library)
            self.logger.info("  Bus library: %s" % args.bus_library)
            Xml2VhdlGenerate(args)
        except:
            self.logger.error("Failed to generate AXI HDL from XML!")
            # Throw whatever error was caught
            raise

    def _gen_hdl_simulink(self, hdl_sysgen_filename):
        """
        This function replaces incorrectly generated simulink sysgen code with the proper code. In this case, the
        dual port ram latency is incorrectly generated when using Vivado 2018.2, 2018.2.2. The code is only replaced if
        the dual port ram is utilised and the 2018.2, 2018.2.2 version is detected.

        :param hdl_sysgen_filename: This is the path and hdl file that
            contains the original sysgen code. This file is overwritten with new latency info before being imported to
            the compile directory
        :type filename_bin: str
        """
        stringToMatch_ver = '2018.2'
        stringToMatchS = '_xldpram'
        stringToMatchA = 'latency_test: if (latency > 6) generate'
        stringToMatchB = 'latency => latency - 6'
        stringToMatchC = 'latency1: if (latency <= 6) generate'

        lines = []
        self.logger.debug('Opening Original hdl file %s' % hdl_sysgen_filename)

        # checks to see if Vivado version is 2018.2 before doing this change
        ver_exists = 'False'
        with open(hdl_sysgen_filename, 'r') as fh1:
            for line in fh1:
                if stringToMatch_ver in line:
                    ver_exists = True
        fh1.close()

        # checks to see if dual port ram is instantiated before doing this change
        dpram_exists = 'False'
        with open(hdl_sysgen_filename, 'r') as fh1:
            for line in fh1:
                if stringToMatchS in line:
                    dpram_exists = True
        fh1.close()

        # If dual port ram exists and version is 2018.2 then, read sysgen code from original file and write appended
        # corrected code to a new list that will be written into a new file
        if dpram_exists == True and ver_exists == True:
            with open(hdl_sysgen_filename, 'r') as fh1:
                for line in fh1:
                    if stringToMatchA in line:
                        linesub = line[:line.find('>') + 2] + '3' + line[line.find('>') + 3:]
                        lines.append(linesub)
                    elif stringToMatchB in line:
                        linesub = line[:line.find('-') + 2] + '3' + line[line.find('-') + 3:]
                        lines.append(linesub)
                    elif stringToMatchC in line:
                        linesub = line[:line.find('=') + 2] + '3' + line[line.find('=') + 3:]
                        lines.append(linesub)
                    else:
                        lines.append(line)
            fh1.close()

            # write updated sysgen code to the same file that will be imported to the correct folder
            with open(hdl_sysgen_filename, 'w') as fh2:
                fh2.writelines(lines)
            fh2.close()
            self.logger.debug('File written. Vivado version is 2018.2: %s. Dual Port RAM exists: %s'
                             % (ver_exists, dpram_exists))
        else:
            self.logger.debug('File not written. Vivado version is 2018.2: %s. Dual Port RAM exists: %s'
                             % (ver_exists, dpram_exists))


class ToolflowFrontend(object):
    """

    """
    def __init__(self, compile_dir='/tmp', target='/tmp/test.slx'):
        """

        :param compile_dir:
        :param target:
        """
        self.logger = logging.getLogger('jasper.toolflow.frontend')
        self.compile_dir = compile_dir
        if not os.path.exists(target):
            self.logger.error('Target path %s does not exist!' % target)
            raise Exception('Target path %s does not exist!' % target)
        self.target = target

    def gen_periph_file(self, fname='jasper.per'):
        """
        Call upon the frontend to generate a
        jasper-standard file defining peripherals
        (yellow blocks) present in a model.

        This method should be overridden by the
        specific frontend of choice, and should
        return the full path to the
        peripheral file.

        Use ``skip = True`` to just return the name of
        the file, without bothering to regenerate it
        (useful for debugging, and future use cases
        where a user only wants to run certain
        steps of a compile)
        """
        raise NotImplementedError()

    def write_git_info_file(self, fname='git_info.tab'):
        """
        Call upon the frontend to generate a
        git info file, which contains the
        git repo information, which is used for
        the header for the fpg file. This function is
        overwritten by the SimulinkFrontEnd Class
        """
        raise NotImplementedError()

    def compile_user_ip(self):
        """
        Compile the user IP to a single HDL module. 
        
        Return the name of this module.

        Should be overridden by each FrontEnd subclass.
        """
        raise NotImplementedError()


class ToolflowBackend(object):
    """

    """
    def __init__(self, plat=None, compile_dir='/tmp'):
        """

        :param plat:
        :param compile_dir:
        """
        self.logger = logging.getLogger('jasper.toolflow.backend')
        self.compile_dir = compile_dir
        self.output_dir = compile_dir + '/outputs'
        self.plat = plat
        self.castro = None
        if plat:
            self.initialize(plat)

    def initialize(self, plat):
        """

        :param plat:
        """
        raise NotImplementedError

    def compile(self, core, plat):
        """

        :param core:
        :param plat:
        """
        raise NotImplementedError

    def add_source(self, source, plat):
        """
        Add a sourcefile to the project. Via a tcl incantation.
        In non-project mode, it is important to note that copies are not made
        of files. The files are read from their source directory. Project mode
        copies files from their source directory and adds them to the a new
        compile directory.
        """
        raise NotImplementedError

    def add_const_file(self, constfile):
        """
        Add a constraint file to the project. via a tcl incantation.
        In non-project mode, it is important to note that copies are not made
        of files. The files are read from their source directory. Project
        mode copies files from their source directory and adds them to the
        a new compile directory.

        :param constfile:
        """
        raise NotImplementedError

    def gen_constraint_file(self, constraints):
        """
        Pass this method a toolflow-standard list of constraints
        which have already had their physical parameters calculated
        and it will generate a constraint file and add it to the
        current project.
        """
        raise NotImplementedError

    def import_from_castro(self, filename):
        import castro
        self.castro = castro.Castro.load(filename)
        existing_sources = []
        for source in self.castro.src_files:
            if source not in existing_sources:
                existing_sources.append(source)
                if not os.path.exists(source):
                    errmsg = 'sourcefile %s doesn\'t exist!' % source
                    self.logger.error(errmsg)
                    raise Exception(errmsg)
                self.add_source(source, self.plat)
        existing_sources = []
        for source in self.castro.synthesis.vendor_constraints_files:
            if source not in existing_sources:
                existing_sources.append(source)
                if not os.path.exists(source):
                    errmsg = 'sourcefile %s doesn\'t exist!' % source
                    self.logger.error(errmsg)
                    raise Exception(errmsg)
                self.add_const_file(source)

        for ip in self.castro.ips:
            self.add_library(ip['path'])
            if 'module_name' in ip:
                self.add_ip(ip)

        # elaborate pin constraints
        for const in self.castro.synthesis.pin_constraints:
            pins = self.plat.get_pins(const.symbolic_name,
                                      const.symbolic_indices)
            numindices = len(const.symbolic_indices)
            const.location = [pins[idx].loc for idx in range(numindices)]
            const.io_standard = [pins[idx].iostd for idx in range(numindices)]
            const.is_vector = const.portname_indices != []

        self.gen_constraint_file(
            self.castro.synthesis.pin_constraints +
            self.castro.synthesis.clk_constraints +
            self.castro.synthesis.gen_clk_constraints +
            self.castro.synthesis.clk_grp_constraints +
            self.castro.synthesis.input_delay_constraints +
            self.castro.synthesis.output_delay_constraints +
            self.castro.synthesis.max_delay_constraints +
            self.castro.synthesis.min_delay_constraints +
            self.castro.synthesis.false_path_constraints +
            self.castro.synthesis.multi_cycle_constraints +
            self.castro.synthesis.raw_constraints)

    def mkfpg(self, filename_bin, filename_fpg):
        """
        This function makes the fpg file header and the final fpg file, which
        consists of the fpg file header (core_info.tab, design_info.tab and
        git_info.tab) and the compressed binary file. The fpg file is used
        to configure the ROACH, ROACH2, MKDIG and SKARAB boards.

        :param filename_bin: This is the path and binary file (top.bin) that
            contains the FPGA programming data.
        :type filename_bin: str
        :param filename_fpg: This is the output time stamped fpg file name
        :type filename_fpg: str
        """
        # files to read from (core_info.tab, design_info.tab and git_info.tab)
        basefile_core = '%s/core_info.tab' % self.compile_dir
        basefile_design = '%s/design_info.tab' % self.compile_dir
        basefile_git = '%s/git_info.tab' % self.compile_dir

        # file, which represents the fpg file header only
        extended_info = '%s/extended_info.kcpfpg' % self.compile_dir

        self.logger.debug('Opening core_info.tab file %s' % basefile_core)
        self.logger.debug('Opening design_info.tab file %s' % basefile_design)
        self.logger.debug('Opening git_info.tab file %s' % basefile_git)

        # read base files and write to fpg header file in correct format
        with open(extended_info, 'w') as fh4:
            fh4.write('#!/bin/kcpfpg\n')
            fh4.write('?uploadbin\n')
            with open(basefile_core, 'r') as fh1:
                for row in fh1:
                    col1, col2, col3, col4 = row.split()
                    fh4.write('?register\t'+col1+'\t0x'+col3+'\t0x'+col4+'\n')
            with open(basefile_design, 'r') as fh2:
                line = fh2.readline()
                while line:
                    fh4.write('?meta\t' + line)
                    line = fh2.readline()
            with open(basefile_git, 'r') as fh3:
                line = fh3.readline()
                while line:
                    fh4.write(line)
                    line = fh3.readline()
        # add the MD5 Checksums here
        with open(extended_info, 'rb') as fh:
            md5_header = hashlib.md5(fh.read()).hexdigest()
        with open(filename_bin, 'rb') as fh:
            bitstream = fh.read()
            # 1) Calculate MD5 Checksum on binary data
            md5_bitstream = hashlib.md5(bitstream).hexdigest()

            # 2) Calculate 'FlashWriteChecksum' to be compared to
            #    SpartanChecksum when upload_to_ram()
            #   - Need to give it the chunk size being used in upload_to_ram
            #   - This alters how the SPARTAN calculates the checksum
            flash_write_checksum = self.calculate_checksum_using_bitstream(
                bitstream, packet_size=MAX_IMAGE_CHUNK_SIZE)

        # add the md5sums, checksum and ?quit to the extended info file
        with open(extended_info, 'a') as fh:
            # Line to write must follow general format, as per Paul
            line = '77777\t77777\tmd5_header\t' + md5_header + '\n'
            fh.write("?meta\t" + line)
            line = '77777\t77777\tmd5_bitstream\t' + md5_bitstream + '\n'
            fh.write("?meta\t" + line)
            line = '77777\t77777\tflash_write_checksum\t' + \
                   str(flash_write_checksum) + '_' + str(MAX_IMAGE_CHUNK_SIZE) + '\n'
            fh.write("?meta\t" + line)
            fh.write('?quit\n')

        # copy binary file from binary file location and rename to system.bin
        mkfpg_cmd1 = 'cp %s %s/system.bin' % (filename_bin, self.compile_dir)
        os.system(mkfpg_cmd1)
        # compress binary file in new location
        mkfpg_cmd2 = 'gzip -c %s/system.bin > %s/system.bin.gz' % (
            self.compile_dir, self.compile_dir)
        os.system(mkfpg_cmd2)
        # append the compressed binary file to the extended_info.kcpfpg file
        mkfpg_cmd3 = 'cat %s/system.bin.gz >> %s/extended_info.kcpfpg' % (
            self.compile_dir, self.compile_dir)
        os.system(mkfpg_cmd3)
        # copy extended_info.kcpfpg and rename to time stamped file and
        # place in output directory with the bof file
        mkfpg_cmd4 = 'cp %s/extended_info.kcpfpg %s/%s' % (
            self.compile_dir, self.output_dir, filename_fpg)
        os.system(mkfpg_cmd4)

    @staticmethod
    def calculate_checksum_using_bitstream(bitstream, packet_size=8192):
        """
        Summing up all the words in the input bitstream, and returning a
        ``Checksum`` - Assuming that the bitstream HAS NOT been padded yet

        :param bitstream: The actual bitstream of the file in question
        :param packet_size: max size of image packets that we pad to
        :return: checksum
        """

        size = len(bitstream)

        flash_write_checksum = 0x00

        for i in range(0, size, 2):
            # This is just getting a substring, need to convert to hex
            two_bytes = bitstream[i:i + 2]
            one_word = struct.unpack('!H', two_bytes)[0]
            flash_write_checksum += one_word

        if (size % packet_size) != 0:
            # padding required
            num_padding_bytes = packet_size - (size % packet_size)
            for i in range(num_padding_bytes // 2):
                flash_write_checksum += 0xffff

        # Last thing to do, make sure it is a 16-bit word
        flash_write_checksum &= 0xffff

        return flash_write_checksum

class SimulinkFrontend(ToolflowFrontend):
    """

    """
    def __init__(self, compile_dir='/tmp', target='/tmp/test.slx'):
        """

        :param compile_dir:
        :param target:
        """
        ToolflowFrontend.__init__(self, compile_dir=compile_dir, target=target)
        if target[-4:] not in ['.slx', '.mdl']:
            self.logger.warning('Frontend target %s does not look like a '
                                'simulink file!' % target)
        self.modelpath = target
        self.modelname = target.split('/')[-1][:-4]  # strip off extension

    def gen_periph_file(self, fname='jasper.per'):
        """
        generate the peripheral file. 
        
        i.e., the list of yellow blocks and their parameters. 
        
        It also generates the ``design_info.tab`` file which is used to populate the fpg file header

        :param fname: The full path and name to give the peripheral file.
        :type fname: str
        """
        self.logger.info('Generating yellow block description file: %s' % fname)
        # change directory to the matlab script directory
        term_cmd = os.getenv('MLIB_DEVEL_PATH')
        os.chdir(term_cmd)
        # The command to start matlab with appropriate libraries
        matlab_start_cmd = os.path.join(os.getenv('XILINX_PATH'), 'bin', 'sysgen')
        #matlab_start_cmd = os.getenv('SYSGEN_SCRIPT')
        # The matlab script responsible for generating the peripheral file
        # each script represents a matlab function
        script1 = 'open_system'
        script2 = 'set_param'
        script3 = 'gen_block_file'
        script4 = 'gen_xps_add_design_info'

        # The matlab syntax to call this script with appropriate args
        # This scripts runs open_system(), set_param(), gen_block_file() and
        # gen_xps_add_design_info().
        # if open_system() and set_param() are not run then the peripheral
        # names will be incorrectly generated and the design will not compile.
        # Everything is run on a single matlab terminal line
        ml_cmd = "%s('%s');sys=gcs;%s(sys,'SimulationCommand','update');" \
                 "%s('%s','%s');mssge.xps_path='%s';" \
                 "%s(sys,mssge,'/');exit" % (script1, self.modelpath, script2,
                                             script3, self.compile_dir, fname,
                                             self.compile_dir, script4)
        # Complete command to run on terminal
        term_cmd = matlab_start_cmd + ' -nodesktop -nosplash -r "%s"' % ml_cmd
        self.logger.info('Running terminal command: %s' % term_cmd)
        os.system(term_cmd)

    def write_git_info_file(self, fname='git_info.tab'):
        """
        Get the git info for mlib_devel and the model file.
        :param fname:
        :return:
        """
        fpath = '%s/%s' % (self.compile_dir, fname)
        fptr = open(fpath, 'w')
        if kat_get_version is None:
            fptr.close()
            return
        model_git = self.modelpath + '\t' + kat_get_version(self.modelpath)
        mlib_git = __file__ + '\t' + kat_get_version(__file__)
        fptr.write('?meta\t77777_git\trcs\t{}\n'.format(model_git))
        fptr.write('?meta\t77777_git\trcs\t{}\n'.format(mlib_git))
        fptr.close()

    def compile_user_ip(self, update=False):
        """
        Compile the users simulink design. The resulting netlist should
        end up in the location already specified in the peripherals file.

        :param update: Update the simulink model before running system generator
        :type update: bool
        """
        self.logger.info('Compiling user IP to module: %s' % self.modelname)
        # change directory to the matlab script directory
        term_cmd = os.getenv('MLIB_DEVEL_PATH')
        os.chdir(term_cmd)
        # The command to start matlab with appropriate libraries
        # matlab_start_cmd = os.getenv('MLIB_DEVEL_PATH') + '/startsg'
        #matlab_start_cmd = os.getenv('SYSGEN_SCRIPT')
        matlab_start_cmd = os.path.join(os.getenv('XILINX_PATH'), 'bin', 'sysgen')
        # The matlab syntax to start a compile with appropriate args
        ml_cmd = "start_sysgen_compile('%s','%s',%d);exit" % (
            self.modelpath, self.compile_dir, int(update))
        term_cmd = matlab_start_cmd + ' -nodesktop -nosplash -r "%s"' % ml_cmd
        self.logger.info('Running terminal command: %s' % term_cmd)
        os.system(term_cmd)

class VivadoBackend(ToolflowBackend):
    """

    """
    def __init__(self, plat=None, compile_dir='/tmp', periph_objs=None):
        """

        :param plat:
        :param compile_dir:
        :param periph_objs:
        """
        self.logger = logging.getLogger('jasper.toolflow.backend')
        self.compile_dir = compile_dir
        self.const_file_ext = 'xdc'
        # src_file parameters for non-project mode only
        self.src_file_vhdl_ext = 'vhd'
        self.src_file_ip_ext = 'xci'
        self.src_file_verilog_ext = 'v'
        self.src_file_sys_verilog_ext = 'sv'
        self.src_file_block_diagram_ext = 'bd'
        self.src_file_elf_ext = 'elf'
        self.src_file_coe_ext = 'coe'
        self.src_file_design_checkpoint_ext = 'dcp'
        self.manufacturer = 'xilinx'
        self.project_name = 'myproj'
        self.periph_objs = periph_objs
        self.tcl_cmd = ''
        # if project mode is enabled
        if plat.project_mode:
            self.binary_loc = '%s/%s/%s.runs/impl_1/top.bin' % (
                self.compile_dir, self.project_name, self.project_name)
            self.hex_loc = '%s/%s/%s.runs/impl_1/top.hex' % (
                self.compile_dir, self.project_name, self.project_name)
            self.mcs_loc = '%s/%s/%s.runs/impl_1/top.mcs' % (
                self.compile_dir, self.project_name, self.project_name)
            self.prm_loc = '%s/%s/%s.runs/impl_1/top.prm' % (
                self.compile_dir, self.project_name, self.project_name)

        # if non-project mode is enabled
        else:
            self.binary_loc = '%s/%s/top.bin' % (
                self.compile_dir, self.project_name)
            self.hex_loc = '%s/%s/top.hex' % (
                self.compile_dir, self.project_name)
            self.mcs_loc = '%s/%s/top.mcs' % (
                self.compile_dir, self.project_name)
            self.prm_loc = '%s/%s/top.prm' % (
                self.compile_dir, self.project_name)

        self.name = 'vivado'
        self.npm_sources = []
        ToolflowBackend.__init__(self, plat=plat, compile_dir=compile_dir)

    def initialize(self, plat):
        self.tcl_cmds = {
            'init'        : '',
            'pre_synth'   : '',
            'synth'       : '',
            'post_synth'  : '',
            'pre_impl'    : '',
            'impl'        : '',
            'post_impl'   : '',
            'pre_bitgen'  : '',
            'bitgen'      : '',
            'post_bitgen' : '',
            'promgen'     : '',
        }

        if plat.manufacturer.lower() != self.manufacturer.lower():
            self.logger.error('Trying to compile a %s FPGA using %s %s' % (
                plat.manufacturer, self.manufacturer, self.name))

        self.add_tcl_cmd('puts "Starting tcl script"')
        # Create Vivado Project in project mode only
        if plat.project_mode:
            self.add_tcl_cmd('create_project -f %s %s/%s -part %s' % (
                self.project_name, self.compile_dir, self.project_name,
                plat.fpga))
        # Create the part in non-project mode (project runs in memory only)
        else:
            self.add_tcl_cmd('file mkdir %s/%s' % (self.compile_dir,
                                                   self.project_name))
            self.add_tcl_cmd('set_part %s' % plat.fpga)
        # Set the project to default to vhdl    
        self.add_tcl_cmd('set_property target_language VHDL [current_project]')    

    def add_library(self, path):
        """
        Add a library at <path>
        """
        self.add_tcl_cmd('set repos [get_property ip_repo_paths [current_project]]')
        self.add_tcl_cmd('set_property ip_repo_paths "$repos %s" [current_project]' % path)
        self.add_tcl_cmd('update_ip_catalog')

    def add_ip(self, ip):
        """
        Add an ip core from a library
        """
        self.add_tcl_cmd('create_ip -name %s -vendor %s -library %s -version %s -module_name %s' % (ip['name'], ip['vendor'], ip['library'], ip['version'], ip['module_name']))

    def add_source(self, source, plat):
        """
        Add a sourcefile to the project. Via a tcl incantation.
        In non-project mode, it is important to note that copies are not made
        of files. The files are read from their source directory. Project mode
        copies files from their source directory and adds them to the a new
        compile directory.
        """
        self.logger.debug('Adding source file: %s' % source)
        # Project Mode is enabled
        if plat.project_mode:
            self.add_tcl_cmd('import_files -force %s' % source)
        # Non-Project Mode is enabled
        else:
            if os.path.basename(source) == 'top.v':
                # Convert from string to Lists and extract filenames from
                # the directory source
                self.npm_sources = os.path.basename(source).split()
            # extract file names from the directories listed in the source
            else:
                self.npm_sources = os.listdir(source)
                self.logger.debug('source %s' % source)
                self.logger.debug('npm_sources %s' % self.npm_sources)
            for item in self.npm_sources:
                ext = item.split('.')[-1]
                current_source = item
                self.logger.debug('extension: %s' % ext)
                self.logger.debug('current_source: %s' % current_source)
                # VHDL File
                if ext == self.src_file_vhdl_ext:
                    self.add_tcl_cmd('read_vhdl %s/%s' % (
                        source, current_source))
                # Verilog File
                elif ext == self.src_file_verilog_ext:
                    # Only read from source when reading the top.v file
                    if os.path.basename(source) == 'top.v':
                        self.add_tcl_cmd('read_verilog %s' % source)
                    else:
                        self.add_tcl_cmd('read_verilog %s/%s' % (
                            source, current_source))
                # System Verilog File
                elif ext == self.src_file_sys_verilog_ext:
                    self.add_tcl_cmd('read_verilog -sv %s/%s' % (source,current_source))
                # IP File
                elif ext == self.src_file_ip_ext:
                    self.add_tcl_cmd('read_ip %s/%s' % (source,current_source))
                # Block Diagram File
                elif ext == self.src_file_block_diagram_ext:
                    self.add_tcl_cmd('read_bd %s/%s' % (source,current_source))
                # ELF Microblaze File
                elif ext == self.src_file_elf_ext:
                    self.add_tcl_cmd('add_files %s/%s' % (source,current_source))
                # Coefficient BRAM File
                elif ext == self.src_file_coe_ext:
                    self.add_tcl_cmd('add_files %s/%s' % (source,current_source))
                # Design checkpoint files
                elif ext == self.src_file_design_checkpoint_ext:
                    self.add_tcl_cmd('add_files %s' % current_source)
                else:
                    self.logger.warning('unknown extension, ignoring source file %s' % current_source)

    def add_const_file(self, constfile):
        """
        Add a constraint file to the project. via a tcl incantation.
        In non-project mode, it is important to note that copies are not made
        of files. The files are read from their source directory. Project
        mode copies files from their source directory and adds them to the
        a new compile directory.

        :param constfile:
        """
        if constfile.split('.')[-1] == self.const_file_ext:
            self.logger.debug('Adding constraint file: %s' % constfile)
            # Project Mode is enabled
            if self.plat.project_mode:
                self.add_tcl_cmd('import_files -force -fileset constrs_1 %s' %
                                 constfile)
            # Non-Project Mode is enabled
            else:
                self.add_tcl_cmd('read_xdc %s' % constfile)
        else:
            self.logger.debug('Ignore constraint file: %s, with wrong file '
                              'extension' % constfile)

    def add_tcl_cmd(self, cmd, stage='pre_synth'):
        """
        Add a command to the tcl command list with
        a trailing newline.
        """
        self.logger.debug('Adding tcl command: %s' % cmd)
        self.tcl_cmds[stage] += cmd
        self.tcl_cmds[stage] += '\n'

    def eval_tcl(self):
        s = ''
        s += self.tcl_cmds['init']
        s += self.tcl_cmds['pre_synth']
        s += self.tcl_cmds['synth']
        s += self.tcl_cmds['post_synth']
        s += self.tcl_cmds['pre_impl']
        s += self.tcl_cmds['impl']
        s += self.tcl_cmds['post_impl']
        s += self.tcl_cmds['pre_bitgen']
        s += self.tcl_cmds['bitgen']
        s += self.tcl_cmds['post_bitgen']
        s += self.tcl_cmds['promgen']
        return s

    def add_compile_cmds(self, cores=8, plat=None, synth_strat=None, impl_strat=None):
        """
        Add the tcl commands for compiling the design, and then launch
        vivado in batch mode
        """
        tcl = self.add_tcl_cmd
        # Project Mode is enabled
        if plat.project_mode:
            # Pre-Synthesis Commands
            self.add_tcl_cmd('set_property top top [current_fileset]', stage='pre_synth')
            self.add_tcl_cmd('update_compile_order -fileset sources_1', stage='pre_synth')
            # Hack to get the System generator RAMs to see their coefficient files.
            # Vivado (2016.1) doesn't seem to import the .coe and ram .xci files in the
            # correct relative directories as configured by System Generator.
            self.add_tcl_cmd('if {[llength [glob -nocomplain [get_property directory [current_project]]/myproj.srcs/sources_1/imports/*.coe]] > 0} {', stage='pre_synth')
            self.add_tcl_cmd('file copy -force {*}[glob [get_property directory [current_project]]/myproj.srcs/sources_1/imports/*.coe] [get_property directory [current_project]]/myproj.srcs/sources_1/ip/', stage='pre_synth')
            self.add_tcl_cmd('}', stage='pre_synth')

            # add the upgrade_ip command to the tcl file if the yaml file requrests it, default to upgrading the IP
            if "upgrade_ip" not in list(sorted(plat.conf.keys())) or plat.conf['upgrade_ip'] == True:
                self.add_tcl_cmd('upgrade_ip -quiet [get_ips *]', stage='pre_synth')
                self.logger.debug('adding the upgrade_ip command to the tcl script')
            else:
                self.logger.debug('The upgrade_ip command is not being added to the tcl script')
            # Add in if ILA is being used to prevent signal names from changing during synthesis
            #self.add_tcl_cmd('set_property STEPS.SYNTH_DESIGN.ARGS.FLATTEN_HIERARCHY none [get_runs synth_1]')

            # Pre-Synthesis Commands
            if synth_strat is not None:
                # synth_strat must be error-checked before arriving here
                self.add_tcl_cmd('set_property strategy {} [get_runs synth_1]'.format(synth_strat), stage='pre_synth')

            # Synthesis Commands
            self.add_tcl_cmd('reset_run synth_1', stage='synth')
            self.add_tcl_cmd('launch_runs synth_1 -jobs %d' % cores, stage='synth')
            self.add_tcl_cmd('wait_on_run synth_1', stage='synth')

            # Post-Synthesis Commands
            self.add_tcl_cmd('open_run synth_1', stage='post_synth')

            # Pre-Implementation Commands
            if impl_strat is not None:
                # impl_strat must be error-checked before arriving here
                self.add_tcl_cmd('set_property strategy {} [get_runs impl_1]'.format(impl_strat), stage='pre_impl')
            self.add_tcl_cmd('set_property STEPS.WRITE_BITSTREAM.ARGS.BIN_FILE true [get_runs impl_1]', stage='pre_impl')
            self.add_tcl_cmd('set_property STEPS.PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]', stage='pre_impl')
            self.add_tcl_cmd('set_property STEPS.POST_ROUTE_PHYS_OPT_DESIGN.IS_ENABLED true [get_runs impl_1]', stage='pre_impl')

            # Implementation Commands
            self.add_tcl_cmd('launch_runs impl_1 -jobs %d' % cores, stage='impl')
            self.add_tcl_cmd('wait_on_run impl_1', stage='impl')

            # Post-Implementation Commands
            self.add_tcl_cmd('open_run impl_1', stage='post_impl')

            # Pre-Bitgen Commands

            # Bitgen Commands
            self.add_tcl_cmd('launch_runs impl_1 -to_step write_bitstream', stage='bitgen')
            self.add_tcl_cmd('wait_on_run impl_1', stage='bitgen')
            self.add_tcl_cmd('cd [get_property DIRECTORY [current_project]]', stage='bitgen')

            # Post-Bitgen Commands
            # Generate a binary file for SKARAB where the bits are reversed per byte. This is used by casperfpga for
            # configuring the FPGA
            try:
                if plat.conf['bit_reversal'] == True:
                    self.add_tcl_cmd('write_cfgmem -force -format bin -interface bpix8 -size 128 -loadbit "up 0x0 '
                                  '%s/%s/%s.runs/impl_1/top.bit" -file %s'
                                   % (self.compile_dir, self.project_name, self.project_name, self.binary_loc), stage='post_bitgen')
            # just ignore if key is not present as only some platforms will have the key.
            except KeyError:
                s = ""
            # Generate a hex and mcs file for SKARAB for the multiboot or golden image. This is used by
            # casperfpga and JTAG for configuring the FPGA
            try:
                if plat.conf['boot_image'] == 'multiboot':
                    self.add_tcl_cmd('write_cfgmem -force -format hex -interface bpix16 -size 128 -loadbit "up 0x0 '
                                 '%s/%s/%s.runs/impl_1/top.bit" -file %s'
                                 % (self.compile_dir, self.project_name, self.project_name, self.hex_loc), stage='post_bitgen')
                    self.add_tcl_cmd('write_cfgmem -force -format mcs -interface bpix16 -size 128 -loadbit "up 0x03000000 '
                                 '%s/%s/%s.runs/impl_1/top.bit" -file %s'
                                 % (self.compile_dir, self.project_name, self.project_name, self.mcs_loc), stage='post_bitgen')
                if plat.conf['boot_image'] == 'golden':
                    self.add_tcl_cmd('write_cfgmem -force -format hex -interface bpix16 -size 128 -loadbit "up 0x0 '
                                 '%s/%s/%s.runs/impl_1/top.bit" -file %s'
                                 % (self.compile_dir, self.project_name, self.project_name, self.hex_loc), stage='post_bitgen')
                    self.add_tcl_cmd('write_cfgmem -force -format mcs -interface bpix16 -size 128 -loadbit "up 0x0 '
                                 '%s/%s/%s.runs/impl_1/top.bit" -file %s'
                                 % (self.compile_dir, self.project_name, self.project_name, self.mcs_loc), stage='post_bitgen')

            # just ignore if key is not present as only some platforms will have the key.
            except KeyError:
                s = ""

            # Determine if the design meets timing or not
            # Look for Worst Negative Slack
            self.add_tcl_cmd('if { [get_property STATS.WNS [get_runs impl_1] ] < 0 } {', stage='post_bitgen')
            self.add_tcl_cmd('puts "Found timing violations => Worst Negative Slack:'
                             ' [get_property STATS.WNS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('} else {', stage='post_bitgen')
            self.add_tcl_cmd('puts "No timing violations => Worst Negative Slack:'
                             ' [get_property STATS.WNS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('}', stage='post_bitgen')
            # Look for Total Negative Slack
            self.add_tcl_cmd('if { [get_property STATS.TNS [get_runs impl_1] ] < 0 } {', stage='post_bitgen')
            self.add_tcl_cmd('puts "Found timing violations => Total Negative Slack:'
                             ' [get_property STATS.TNS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('} else {', stage='post_bitgen')
            self.add_tcl_cmd('puts "No timing violations => Total Negative Slack:'
                             ' [get_property STATS.TNS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('}', stage='post_bitgen')
            # Look for Worst Hold Slack
            self.add_tcl_cmd('if { [get_property STATS.WHS [get_runs impl_1] ] < 0 } {', stage='post_bitgen')
            self.add_tcl_cmd('puts "Found timing violations => Worst Hold Slack:'
                             ' [get_property STATS.WHS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('} else {', stage='post_bitgen')
            self.add_tcl_cmd('puts "No timing violations => Worst Hold Slack:'
                             ' [get_property STATS.WHS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('}', stage='post_bitgen')
            # Look for Total Hold Slack
            self.add_tcl_cmd('if { [get_property STATS.THS [get_runs impl_1] ] < 0 } {', stage='post_bitgen')
            self.add_tcl_cmd('puts "Found timing violations => Total Hold Slack:'
                             ' [get_property STATS.THS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('} else {', stage='post_bitgen')
            self.add_tcl_cmd('puts "No timing violations => Total Hold Slack:'
                             ' [get_property STATS.THS [get_runs impl_1]] ns" ', stage='post_bitgen')
            self.add_tcl_cmd('}', stage='post_bitgen')

            # Let Yellow Blocks add their own tcl commands
            self.gen_yellowblock_tcl_cmds()
            # Let Yellow Blocks add their own HDL files
            self.gen_yellowblock_custom_hdl()
            # add source files to the project from the compile directory
            self.gen_add_compile_dir_source_tcl_cmds()

        # Non-Project mode is enabled
        # Options can be added to the *_design commands to change strategies
        # or meet timing
        else:
            proj_path = '%s/%s' % (self.compile_dir, self.project_name)
            tcl('synth_design -top top -part %s' % plat.fpga)
            tcl('write_checkpoint -force %s/post_synth.dcp' % proj_path)
            tcl('report_timing_summary -file %s/post_synth_timing_summary.'
                'rpt' % proj_path)
            tcl('report_utilization -file %s/post_synth_timing_summary.'
                'rpt' % proj_path)
            tcl('opt_design')
            tcl('place_design')
            tcl('report_clock_utilization -file %s/clock_util.rpt' % proj_path)
            # Run power_opt_design and phys_opt_design if setup timing
            # violations occur
            tcl('if { [get_property SLACK [get_timing_paths -max_paths 1 '
                '-nworst 1 -setup] ] < 0 } {')
            tcl('puts "Found setup timing violations => running physical '
                'optimization" ')
            tcl('power_opt_design')
            tcl('phys_opt_design')
            tcl('}')
            # Run power_opt_design and phys_opt_design if hold timing
            # violations occur
            tcl('if { [get_property SLACK [get_timing_paths -max_paths 1 '
                '-nworst 1 -hold] ] < 0 } {')
            tcl('puts "Found hold timing violations => running physical '
                'optimization" ')
            tcl('power_opt_design')
            tcl('phys_opt_design')
            tcl('}')
            tcl('write_checkpoint -force %s/post_place.dcp' % proj_path)
            tcl('report_utilization -file %s/post_place_util.rpt' % proj_path)
            tcl('report_timing_summary -file %s/post_place_timing_summary.'
                'rpt' % proj_path)
            tcl('route_design')
            tcl('write_checkpoint -force %s/post_route.dcp' % proj_path)
            tcl('report_route_status -file %s/post_route_status.'
                'rpt' % proj_path)
            tcl('report_timing_summary -file %s/post_route_timing_summary.'
                'rpt' % proj_path)
            tcl('report_power -file %s/post_route_power.rpt' % proj_path)
            tcl('report_drc -file %s/post_imp_drc.rpt' % proj_path)
            tcl('set_property SEVERITY {Warning} [get_drc_checks UCIO-1]')
            tcl('write_bitstream -force -bin_file %s/top.bit' % proj_path)
            # Generate a binary file for SKARAB where the bits are reversed
            # per byte. This is used by casperfpga for configuring the FPGA
            try:
                if plat.conf['bit_reversal']:
                    tcl('write_cfgmem -force -format bin -interface bpix8 '
                        '-size 128 -loadbit "up 0x0 %s/%s/top.bit" -file %s' % (
                            self.compile_dir, self.project_name,
                            self.binary_loc))
            # just ignore if key is not present as only some platforms
            # will have the key.
            except KeyError as e:
                raise KeyError(e.message)

            # Generate a hex and mcs file for SKARAB for the multiboot or golden
            # images. This is used by casperfpga and JTAG for configuring the FPGA
            try:
                if plat.conf['boot_image'] == 'multiboot':
                    tcl('write_cfgmem -force -format hex -interface bpix16 '
                        '-size 128 -loadbit "up 0x0 %s/%s/top.bit" -file %s' % (
                            self.compile_dir, self.project_name,
                            self.hex_loc))
                    tcl('write_cfgmem -force -format mcs -interface bpix16 '
                        '-size 128 -loadbit "up 0x03000000 %s/%s/top.bit" -file %s' % (
                            self.compile_dir, self.project_name,
                            self.mcs_loc))
                if plat.conf['boot_image'] == 'golden':
                    tcl('write_cfgmem -force -format hex -interface bpix16 '
                        '-size 128 -loadbit "up 0x0 %s/%s/top.bit" -file %s' % (
                            self.compile_dir, self.project_name,
                            self.hex_loc))
                    tcl('write_cfgmem -force -format mcs -interface bpix16 '
                        '-size 128 -loadbit "up 0x0 %s/%s/top.bit" -file %s' % (
                            self.compile_dir, self.project_name,
                            self.mcs_loc))
            # just ignore if key is not present as only some platforms
            # will have the key.
            except KeyError as e:
                raise KeyError(e.message)


            # Determine if the design meets timing or not
            # Check for setup timing violations
            tcl('if { [get_property SLACK [get_timing_paths -max_paths 1 '
                '-nworst 1 -setup] ] < 0 } {')
            tcl('puts "Found setup timing violations => Worst Setup Slack: '
                '[get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 '
                '-setup]] ns" ')
            tcl('} else {')
            tcl('puts "No setup timing violations => Worst Setup Slack: '
                '[get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 '
                '-setup]] ns" ')
            tcl('}')
            # Check for hold timing violations
            tcl('if { [get_property SLACK [get_timing_paths -max_paths 1 '
                '-nworst 1 -hold] ] < 0 } {')
            tcl('puts "Found setup timing violations => Worst Hold Slack: '
                '[get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 '
                '-hold]] ns" ')
            tcl('} else {')
            tcl('puts "No setup timing violations => Worst Hold Slack: '
                '[get_property SLACK [get_timing_paths -max_paths 1 -nworst 1 '
                '-hold]] ns" ')
            tcl('}')

    def compile(self, cores, plat, synth_strat=None, impl_strat=None):
        """

        :param cores:
        :param plat:
        :param impl_strat: Implementation Strategy to use when
                            carrying out the implementation run 'impl'
        """
        self.add_compile_cmds(cores=cores, plat=plat, synth_strat=synth_strat, impl_strat=impl_strat)
        # write tcl command to file
        tcl_file = self.compile_dir+'/gogogo.tcl'
        helpers.write_file(tcl_file, self.eval_tcl())

        rv = os.system('vivado -jou {cdir}/vivado.jou -log {cdir}/vivado.log '
                       '-mode batch -source '
                       '{cfile}'.format(cdir=self.compile_dir, cfile=tcl_file))
        if rv:
            raise Exception('Vivado failed!')

    def get_tcl_const(self, const):
        """
        Pass a single toolflow-standard PortConstraint,
        and get back a tcl command to add the constraint
        to a vivado project.
        """
        user_const = ''
        if isinstance(const, castro.PinConstraint):
            self.logger.debug('New PortConstraint instance found: %s -> %s' % (
                const.portname, const.symbolic_name))
            for idx, p in enumerate(const.symbolic_indices):
                self.logger.debug('Getting loc for port index %d' % idx)
                loc = const.location[idx]
                if loc is not None:
                    self.logger.debug('LOC constraint found at %s' % loc)
                    user_const += self.format_const(
                        'PACKAGE_PIN', loc, const.portname,
                        index=const.portname_indices[idx] if
                        const.portname_indices else None)

            for idx, p in enumerate(const.symbolic_indices):
                self.logger.debug('Getting iostd for port index %d' % idx)
                iostd = const.io_standard[idx]
                if iostd is not None:
                    self.logger.debug('IOSTD constraint found: %s' % iostd)
                    user_const += self.format_const(
                        'IOSTANDARD', iostd, const.portname,
                        index=const.portname_indices[idx]
                        if const.portname_indices else None)

        if isinstance(const, castro.ClkConstraint):
            self.logger.debug('New Clock constraint found')
            user_const += self.format_clock_const(const)

        if isinstance(const, castro.GenClkConstraint):
            self.logger.debug('New Generated Clock constraint found')
            user_const += self.format_gen_clock_const(const)

        if isinstance(const, castro.ClkGrpConstraint):
            self.logger.debug('New Clock group constraint found')
            user_const += self.format_clock_group_const(const)

        if isinstance(const, castro.InDelayConstraint):
            self.logger.debug('New Input delay constraint found')
            user_const += self.format_input_delay_const(const)

        if isinstance(const, castro.OutDelayConstraint):
            self.logger.debug('New Output delay constraint found')
            user_const += self.format_output_delay_const(const)

        if isinstance(const, castro.MaxDelayConstraint):
            self.logger.debug('New Max delay constraint found')
            user_const += self.format_max_delay_const(const)

        if isinstance(const, castro.MinDelayConstraint):
            self.logger.debug('New Min delay constraint found')
            user_const += self.format_min_delay_const(const)

        if isinstance(const, castro.FalsePthConstraint):
            self.logger.debug('New False Path constraint found')
            user_const += self.format_false_path_const(const)

        if isinstance(const, castro.MultiCycConstraint):
            self.logger.debug('New Multi Cycle constraint found')
            user_const += self.format_multi_cycle_const(const)

        if isinstance(const, castro.RawConstraint):
            self.logger.debug('New Raw constraint found')
            user_const += const.raw

        return user_const

    @staticmethod
    def format_clock_const(c):
        if c.virtual_en:
            return 'create_clock -period %4.3f -name %s -waveform {%4.3f ' \
                   '%4.3f}\n' % (c.period_ns, c.clkname, c.waveform_min_ns,
                                 c.waveform_max_ns)
        elif c.port_en:
            return 'create_clock -period %4.3f -name %s -waveform {%4.3f ' \
                   '%4.3f} [get_ports {%s}]\n' % (c.period_ns, c.clkname,
                                                  c.waveform_min_ns,
                                                  c.waveform_max_ns, c.portname)
        else:
            return 'create_clock -period %4.3f -name %s -waveform {%4.3f ' \
                   '%4.3f} [get_pins {%s}]\n' % (c.period_ns, c.clkname,
                                                 c.waveform_min_ns,
                                                 c.waveform_max_ns, c.portname)

    @staticmethod
    def format_gen_clock_const(c):
        return 'create_generated_clock -name %s -source [get_pins {%s}] ' \
               '-divide_by %d [get_pins {%s}]\n' % (c.clkname, c.clksource,
                                                    c.divide_by, c.pinname)

    @staticmethod
    def format_clock_group_const(c):
        return 'set_clock_groups -%s -group [get_clocks %s] -group ' \
               '[get_clocks %s]\n' % (c.clkdomaintype, c.clknamegrp1,
                                      c.clknamegrp2)

    @staticmethod
    def format_input_delay_const(c):
        if c.add_delay_en:
            return 'set_input_delay -clock [get_clocks %s] -%s -add_delay ' \
                   '%4.3f [get_ports {%s}]\n' % (c.clkname, c.consttype,
                                                 c.constdelay_ns, c.portname)
        else:
            return 'set_input_delay -clock [get_clocks %s] -%s %4.3f ' \
                   '[get_ports {%s}]\n' % (c.clkname, c.consttype,
                                           c.constdelay_ns, c.portname)

    @staticmethod
    def format_output_delay_const(c):
        if c.add_delay_en:
            return 'set_output_delay -clock [get_clocks %s] -%s -add_delay ' \
                   '%4.3f [get_ports {%s}]\n' % (c.clkname, c.consttype,
                                                 c.constdelay_ns, c.portname)
        else:
            return 'set_output_delay -clock [get_clocks %s] -%s %4.3f ' \
                   '[get_ports {%s}]\n' % (c.clkname, c.consttype,
                                           c.constdelay_ns, c.portname)

    @staticmethod
    def format_max_delay_const(c):
        if c.sourcepath is None:
             return 'set_max_delay %s -to %s\n' % (c.constdelay_ns, c.destpath)
        elif c.destpath is None:
             return 'set_max_delay %s -from %s\n' % (c.constdelay_ns, c.sourcepath)
        else:
             return 'set_max_delay %s -from %s -to %s\n' % (c.constdelay_ns, c.sourcepath, c.destpath)

    @staticmethod
    def format_min_delay_const(c):
        if c.sourcepath is None:
             return 'set_min_delay %s -to %s\n' % (c.constdelay_ns, c.destpath)
        elif c.destpath is None:
             return 'set_min_delay %s -from %s\n' % (c.constdelay_ns, c.sourcepath)
        else:
             return 'set_min_delay %s -from %s -to %s\n' % (c.constdelay_ns, c.sourcepath, c.destpath)

    @staticmethod
    def format_false_path_const(c):
        if c.sourcepath is None:
            return 'set_false_path -to %s\n' % c.destpath
        elif c.destpath is None:
            return 'set_false_path -from %s\n' % c.sourcepath
        else:
            return 'set_false_path -from %s -to %s\n' % (c.sourcepath,
                                                         c.destpath)

    @staticmethod
    def format_multi_cycle_const(c):
        return 'set_multicycle_path -%s -from [%s] -to [%s] %d\n' % (
            c.multicycletype, c.sourcepath, c.destpath, c.multicycledelay)

    @staticmethod
    def format_const(attribute, val, port, index=None):
        """
        Generate a tcl syntax command from an attribute, value and port
        (with indexing if required)
        """
        return 'set_property %s %s [get_ports %s%s]\n' % (
                attribute, val, port,
                '[%d]' % index if index is not None else '')

    @staticmethod
    def format_cfg_const(attribute, val):
        """
        Generate a configuration tcl syntax command from an attribute and value
        """
        return 'set_property %s %s [current_design]\n' % (attribute, val)

    def gen_yellowblock_tcl_cmds(self):
        """
        Compose a list of tcl commands from each yellow block.
        To be added to the final tcl script.
        """
        self.logger.info('Extracting yellow block tcl commands'
                         ' from peripherals')
        for obj in self.periph_objs:
            c = obj.gen_tcl_cmds()
            for key, val in c.items():
                if val is not None:
                    for v in val:
                        self.add_tcl_cmd(v, stage=key)

    def gen_yellowblock_custom_hdl(self):
        """
        Create each yellowblock's custom hdl files and add them to the projects sources
        """
        self.logger.info('Generating yellow block custom hdl files')
        for obj in self.periph_objs:
            c = obj.gen_custom_hdl()
            for key, val in c.items():
                # create file and write the source string to it
                f = open('%s/%s' %(self.compile_dir, key),"w")
                f.write(val)
                f.close()
                # add the tcl command to add the source to the project
                self.add_source('%s/%s' %(self.compile_dir, key), self.plat)

    def gen_add_compile_dir_source_tcl_cmds(self):
        """
        Run each blocks add_compile_dir_source functions and add them to the projects sources
        """
        self.logger.info('Generating yellow block custom hdl files')
        for obj in self.periph_objs:
            c = obj.add_build_dir_source()
            for d in c:
                #self.add_source('%s/%s' %(self.compile_dir, d['files']), self.plat)
                self.add_tcl_cmd('import_files %s/%s' %(self.compile_dir, d['files']), stage='pre_synth')
                #if d['library'] != '':
                    # add the source to a library if the library key exists
                #    self.add_tcl_cmd('set_property library %s [get_files  {%s/%s%s}]' %(d['library'], self.compile_dir, d['files'], '*' if d['files'][-1]=='/' else ''), stage='pre_synth')
        self.add_tcl_cmd('update_compile_order -fileset sources_1')

    def gen_constraint_file(self, constraints):
        """
        Pass this method a toolflow-standard list of constraints
        which have already had their physical parameters calculated
        and it will generate a constraint file and add it to the
        current project.
        """
        constfile = '%s/user_const.xdc' % self.compile_dir
        user_const = ''
        for constraint in constraints:
            self.logger.info('parsing constraint %s' % constraint)
            user_const += self.get_tcl_const(constraint)
        self.logger.info("Constraints: %s" % user_const)
        helpers.write_file(constfile, user_const)
        self.logger.info('Finished writing constraints file: %s' % constfile)
        self.add_const_file(constfile)

class ISEBackend(VivadoBackend):
    """

    """
    def __init__(self, plat=None, compile_dir='/tmp'):
        """

        :param plat:
        :param compile_dir:
        """
        self.logger = logging.getLogger('jasper.toolflow.backend')
        self.compile_dir = compile_dir
        self.const_file_ext = 'ucf'
        self.manufacturer = 'xilinx'
        self.project_name = 'myproj'
        self.name = 'ise'
        self.binary_loc = '%s/%s/%s.runs/impl_1/top.bin' % (
            self.compile_dir, self.project_name, self.project_name)
        ToolflowBackend.__init__(self, plat=plat, compile_dir=compile_dir)

    def add_compile_cmds(self, cores=8, plat=None):
        """
        add the tcl commands for compiling the design, and then launch
        vivado in batch mode
        """
        tcl = self.add_tcl_cmd
        tcl('set_property -name {steps.bitgen.args.More Options} -value '
            '{-g Binary:Yes} -objects [get_runs impl_1]')
        tcl('reset_run synth_1')
        tcl('launch_runs synth_1')
        tcl('wait_on_run synth_1')
        tcl('launch_runs impl_1 -to_step BitGen')
        tcl('wait_on_run impl_1')
        # Generate timing report. There is no way to read back the timing paths.
        # 'get_timing_paths' is not recognised in ISE PlanAhead, so reports
        # are generated. The report will indicate whether the timing has
        # failed or not.
        tcl('open_run [get_runs impl_1]')
        tcl('puts "Report setup timing" ')
        tcl('report_timing -max_paths 1 -nworst 1 -setup')
        tcl('report_timing -name setup1 -max_paths 1 -nworst 1 -setup')
        tcl('write_timing setup1 -force %s/%s/%s.runs/impl_1/setup_timing_'
            'analysis.rpt' % (self.compile_dir, self.project_name,
                              self.project_name))
        tcl('puts "Report hold timing" ')
        tcl('report_timing -max_paths 1 -nworst 1 -hold')
        tcl('report_timing -name hold1 -max_paths 1 -nworst 1 -hold')
        tcl('write_timing hold1 -force %s/%s/%s.runs/impl_1/hold_timing_'
            'analysis.rpt' % (self.compile_dir, self.project_name,
                              self.project_name))
        tcl('exit')

    def compile(self, cores, plat):
        """

        """
        self.add_compile_cmds()
        # write tcl command to file
        tcl_file = self.compile_dir+'/gogogo.tcl'
        helpers.write_file(tcl_file, self.tcl_cmd)
        # os.system('vivado -mode batch -source %s'%(tcl_file))
        os.system('planAhead -jou %s/planahead.jou -log %s/planahead.log '
                  '-mode tcl -source %s' % (self.compile_dir,
                                            self.compile_dir, tcl_file))

    @staticmethod
    def format_const(attribute, val, port, index=None):
        """
        Generate a tcl syntax command from an attribute, value and port
        (with indexing if required)
        """
        if index is None:
            return 'NET "%s" %s = "%s";\n' % (port, attribute, val)
        else:
            return 'NET %s<%d> %s = "%s";\n' % (port, index, attribute, val)

    def gen_constraint_file(self, constraints):
        """
        Pass this method a toolflow-standard list of constraints
        which have already had their physical parameters calculated
        and it will generate a contstraint file and add it to the
        current project.
        """
        constfile = '%s/user_const.ucf' % self.compile_dir
        user_const = ''
        for constraint in constraints:
            self.logger.info('parsing constraint %s' % constraint)
            user_const += self.get_ucf_const(constraint)
        self.logger.info("Constraints: %s" % user_const)
        helpers.write_file(constfile, user_const)
        self.logger.info('Finished writing constraints file: %s' % constfile)
        self.add_const_file(constfile)

    def get_ucf_const(self, const):
        """
        Pass a single toolflow-standard PortConstraint,
        and get back a tcl command to add the constraint
        to a vivado project.
        """
        user_const = ''
        if isinstance(const, castro.PinConstraint):
            self.logger.debug('New PortConstraint instance found: %s -> '
                              '%s' % (const.portname, const.symbolic_name))
            for idx, p in enumerate(const.symbolic_indices):
                self.logger.debug('Getting loc for port index %d' % idx)
                loc = const.location[idx]
                if loc is not None:
                    self.logger.debug('LOC constraint found at %s' % loc)
                    user_const += self.format_const(
                        'LOC', loc, const.portname,
                        index=p if const.portname_indices else None)

            for idx, p in enumerate(const.symbolic_indices):
                self.logger.debug('Getting iostd for port index %d' % idx)
                iostd = const.io_standard[idx]
                if iostd is not None:
                    self.logger.debug('IOSTD constraint found: %s' % iostd)
                    user_const += self.format_const(
                        'IOSTANDARD', iostd, const.portname,
                        index=p if const.portname_indices else None)

        if isinstance(const, castro.ClkConstraint):
            self.logger.debug('New Clock constraint found')
            user_const += self.format_clock_const(const)

        if isinstance(const, RawConstraint):
            self.logger.debug('New Raw constraint found')
            user_const += const.raw

        return user_const

    @staticmethod
    def format_clock_const(c):
        return 'NET "%s" TNM_NET = "%s";\nTIMESPEC "TS_%s" = PERIOD ' \
               '"%s" %f ns HIGH 50 %s;\n' % (c.portname, c.portname + '_grp',
                                             c.portname, c.portname + '_grp',
                                             c.period_ns, '%')

# end
