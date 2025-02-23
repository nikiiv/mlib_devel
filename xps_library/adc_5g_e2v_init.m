function adc_5g_e2v_init(blk, varargin)
% Initialize and configure the E2V 5 GSps ADC

defaults = {...
            'adc_mode', '2-Channel',...
            'chips_num', '1',...
            'adc_loc','FMC1',...
            'f_sample','1000'};
 myname=gcb;

 %defaults = { ...
 %   'block_name', blk, ...
 % };

% Check to see if mask parameters have changed
if same_state(blk, 'gcb', gcb, 'defaults', defaults, varargin{:}), return, end
check_mask_type(blk, 'E2V_5g_adc');
munge_block(blk, varargin{:});

adc_mode = get_var('adc_mode', 'defaults', defaults, varargin{:}); 
chips_num= get_var('chips_num', 'defaults', defaults, varargin{:});
adc_loc= get_var('adc_loc', 'defaults', defaults, varargin{:});
f_sample= get_var('f_sample', 'defaults', defaults, varargin{:});
%adc_mode = get_param(myname, 'adc_mode');

if strcmp(adc_mode, '1-Channel'),
    inputs = {'a'};
elseif strcmp(adc_mode, '2-Channel'),
    inputs = {'a', 'c'};
elseif strcmp(adc_mode, '4-Channel'),
    inputs = {'a', 'b', 'c', 'd'};
else 
    error(['Unsupported adc mode: ',adc_mode]);
end
chips_num = str2num(get_param(blk, 'chips_num'));

adc_bit_width=10;
port_names = {...
    'data_a0',...
    'data_a1',...
    'data_a2',...
    'data_a3',...
    'data_b0',...
    'data_b1',...
    'data_b2',...
    'data_b3',...
    'data_c0',...
    'data_c1',...
    'data_c2',...
    'data_c3',...
    'data_d0',...
    'data_d1',...
    'data_d2',...
    'data_d3'};
samples = length(port_names)/length(inputs);
sample_sep = 60;

% Remove all lines, will be redrawn later
delete_lines(blk);

% Load the need libraries (just in case)
%load_system('simulink');
%load_system('simulink/Discrete');
%load_system('dspsigops');

% First, loop over the inputs

for n=0:chips_num-1
 for i=0:length(inputs)-1
    
    curr_x = 30+n*1000;
    % Draw the input with appropriate name
    reuse_block(blk, [...
        'ch',num2str(n),'_','sim_', inputs{i+1}],...
        'built-in/inport',...
        'Position', [curr_x 100+i*sample_sep*samples,...
                     curr_x+30 116+i*sample_sep*samples],...
        'Port', num2str(i+1+n*4));
    
    curr_x = curr_x + 70;
    % Set the input gains and connect to inports
    reuse_block(blk, [...
        'ch',num2str(n),'_','gain_', inputs{i+1}], ...
        'built-in/Gain',...
        'Position', [curr_x 100+i*sample_sep*samples,...
                     curr_x+30 116+i*sample_sep*samples],...
        'Gain', num2str(2^(adc_bit_width-1)));
    add_line(blk, ['ch',num2str(n),'_','sim_', inputs{i+1}, '/1'],...
                  ['ch',num2str(n),'_','gain_', inputs{i+1}, '/1']);
              
    curr_x = curr_x + 70;
    % Add the bias blocks and connect to the gains
    reuse_block(blk, [...
        'ch',num2str(n),'_','bias_', inputs{i+1}], ...
        'built-in/Bias',...
        'Position', [curr_x 100+i*sample_sep*samples,...
                     curr_x+30 116+i*sample_sep*samples],...
        'Bias', num2str(2^(adc_bit_width-1)));
    add_line(blk, ['ch',num2str(n),'_','gain_', inputs{i+1}, '/1'],...
                  ['ch',num2str(n),'_','bias_', inputs{i+1}, '/1']);
    
    % Now, loop over the sample streams
    for j=0:samples-1
        
        curr_x = curr_x + 130;
        % Add downsample blocks
        reuse_block(blk, [...
            'ch',num2str(n),'_','downsample_', inputs{i+1}, num2str(j)], ...
            'dspsigops/Downsample',...
            'Position', [curr_x 100+i*sample_sep*samples+j*sample_sep,...
                         curr_x+30 116+i*sample_sep*samples+j*sample_sep],...
            'N', num2str(samples),...
            'phase', num2str(j),...
            'ic', '0');

        % Try to set options required for Downsample block of newer DSP blockset
        % versions, but not available in older versions.
        try
          set_param([blk, '/ch',num2str(n),'_','downsample_', inputs{i+1}, num2str(j)], ...
            'InputProcessing', 'Elements as channels (sample based)', ...
            'RateOptions', 'Allow multirate processing');
        catch
        end;

        add_line(blk, ['ch',num2str(n),'_','bias_', inputs{i+1}, '/1'],...
                      ['ch',num2str(n),'_','downsample_', inputs{i+1}, num2str(j), '/1']);
              
        curr_x = curr_x + 120;
        % Add delay blocks to align the samples
        if j==0
            delay = 2;
        else
            delay = 1;
        end
        reuse_block(blk, [...
            'ch',num2str(n),'_','delay_', inputs{i+1}, num2str(j)], ...
            'simulink/Discrete/Integer Delay',...
            'Position', [curr_x 100+i*sample_sep*samples+j*sample_sep,...
                         curr_x+30 116+i*sample_sep*samples+j*sample_sep],...
            'NumDelays', num2str(delay),...
            'vinit', '0');
        add_line(blk, ['ch',num2str(n),'_','downsample_', inputs{i+1}, num2str(j), '/1'],...
                      ['ch',num2str(n),'_','delay_', inputs{i+1}, num2str(j), '/1']);
        
        curr_x = curr_x + 120;
        % Add the gateway-in ports, should match the netlist port names
        port_name = clear_name([gcb, '_', 'ch',num2str(n),'_',port_names{i*samples + j + 1}]);
        reuse_block(blk,...
            port_name,...
            'xbsIndex_r4/Gateway In',...
            'Position', [curr_x 100+i*sample_sep*samples+j*sample_sep,...
                         curr_x+80 116+i*sample_sep*samples+j*sample_sep],...
            'arith_type', 'Unsigned',...
            'n_bits', num2str(adc_bit_width),...
            'bin_pt', '0',...
            'overflow', 'Wrap',...
            'quantization', 'Truncate');
        add_line(blk, ['ch',num2str(n),'_','delay_', inputs{i+1}, num2str(j), '/1'],...
                      [port_name, '/1']);
        
        curr_x = curr_x + 160;
        % Now, let's do the output ports!
        reuse_block(blk,...
            ['ch',num2str(n),'_',inputs{i+1}, num2str(j)],...
            'built-in/outport',...
            'Position', [curr_x 100+i*sample_sep*samples+j*sample_sep,...
                         curr_x+30 116+i*sample_sep*samples+j*sample_sep],...
            'Port', num2str(i*samples + j + 1+n*16));
        add_line(blk, [port_name, '/1'],...
                      ['ch',num2str(n),'_',inputs{i+1}, num2str(j), '/1']);
    
        curr_x = curr_x - 530; % undo all x changes
        
    end
    
 end
end

curr_x = 30;
curr_y = 160+i*sample_sep*samples+j*sample_sep;
% Let's do the sync stream
% First, the input port

reuse_block(blk,...
    'sim_sync',...
    'built-in/inport',...
    'Position', [curr_x curr_y,...
                 curr_x+30 16+curr_y],...
    'Port', num2str((i+1)*(n+1)+1));

curr_x = curr_x + 80;
% Now the gateway-in for the sync
sync_name = clear_name([gcb, '_', 'sync']);
reuse_block(blk,...
	sync_name,...
    'xbsIndex_r4/Gateway In',...
    'Position', [curr_x curr_y,...
                 curr_x+80 curr_y+16],...
    'arith_type', 'Boolean');
add_line(blk, 'sim_sync/1', [sync_name, '/1']);

curr_x = curr_x + 180;
% And lastly the output port
reuse_block(blk,...
    'sync_out',...
    'built-in/outport',...
    'Position', [curr_x curr_y,...
                 curr_x+30 curr_y+16],...
    'Port', num2str(length(port_names)*(n+1)+1));
add_line(blk, [sync_name, '/1'], 'sync_out/1');

% adc_clk_out
curr_x = 30;
curr_y = curr_y+60;

reuse_block(blk,...
    'sim_ad_clk',...
    'built-in/inport',...
    'Position', [curr_x curr_y,...
                 curr_x+30 16+curr_y],...
    'Port', num2str((i+1)*(n+1)+2));

curr_x = curr_x + 80;
% Now the gateway-in for the sync
ad_clk_name = clear_name([gcb, '_', 'ad_clk']);
reuse_block(blk,...
	ad_clk_name,...
    'xbsIndex_r4/Gateway In',...
    'Position', [curr_x curr_y,...
                 curr_x+80 curr_y+16],...
    'arith_type', 'Boolean');
add_line(blk, 'sim_ad_clk/1', [ad_clk_name, '/1']);

curr_x = curr_x + 180;
% And lastly the output port
reuse_block(blk,...
    'ad_clk_out',...
    'built-in/outport',...
    'Position', [curr_x curr_y,...
                 curr_x+30 curr_y+16],...
    'Port', num2str(length(port_names)*(n+1)+2));
add_line(blk, [ad_clk_name, '/1'], 'ad_clk_out/1');


clean_blocks(blk);
save_state(blk, 'gcb', gcb, 'defaults', defaults, varargin{:});

